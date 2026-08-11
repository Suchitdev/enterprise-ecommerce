from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse

from reportlab.pdfgen import canvas

from accounts.models import Address
from products.models import Product
from .models import Order, OrderItem, Coupon
from django.db.models import Q

import razorpay
from django.conf import settings


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user):
    return user.is_staff or user.is_superuser


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(request):

    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    # ========================================================
    # CALCULATE CART TOTAL
    # ========================================================

    for product_id, quantity in cart.items():

        try:
            product = Product.objects.get(
                id=product_id
            )

        except Product.DoesNotExist:
            continue

        if quantity > product.stock:

            messages.error(
                request,
                f"Only {product.stock} item(s) of "
                f"'{product.name}' are available in stock."
            )

            return redirect("cart")

        subtotal = (
            product.discount_price * quantity
        )

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    # ========================================================
    # ADDRESSES
    # ========================================================

    addresses = Address.objects.filter(
        user=request.user
    )

    # ========================================================
    # COUPON INFORMATION
    # ========================================================

    discount_amount = request.session.get(
        "discount_amount",
        0
    )

    final_total = request.session.get(
        "final_total",
        total
    )

    coupon_code = request.session.get(
        "coupon_code"
    )

    if final_total < 0:
        final_total = 0

    # ========================================================
    # PLACE ORDER
    # ========================================================

    if request.method == "POST":

        address = get_object_or_404(
            Address,
            id=request.POST.get("address"),
            user=request.user,
        )

        payment_method = request.POST.get(
            "payment"
        )

        # ====================================================
        # CREATE ORDER
        # ====================================================

        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=final_total,
            payment_method=payment_method,
            payment_status="Pending",
            order_status="Pending",
        )

        # ====================================================
        # CREATE ORDER ITEMS + REDUCE STOCK
        # ====================================================

        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price=item["product"].discount_price,
            )

            product = item["product"]

            product.stock -= item["quantity"]

            if product.stock <= 0:

                product.stock = 0
                product.is_available = False

            product.save()

        # ====================================================
        # ONLINE PAYMENT - RAZORPAY
        # ====================================================

        if payment_method == "ONLINE":

            client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET,
                )
            )

            payment = client.order.create({
                "amount": int(
                    final_total * 100
                ),
                "currency": "INR",
                "payment_capture": 1,
            })

            order.razorpay_order_id = payment["id"]

            order.save()

            return render(
                request,
                "payment.html",
                {
                    "order": order,
                    "payment": payment,
                    "razorpay_key": (
                        settings.RAZORPAY_KEY_ID
                    ),
                },
            )

        # ====================================================
        # CASH ON DELIVERY
        # ====================================================

        request.session["cart"] = {}

        request.session.pop(
            "coupon_code",
            None
        )

        request.session.pop(
            "discount_amount",
            None
        )

        request.session.pop(
            "final_total",
            None
        )

        messages.success(
            request,
            "Order placed successfully!"
        )

        return redirect("orders")

    # ========================================================
    # CHECKOUT PAGE
    # ========================================================

    return render(
        request,
        "checkout.html",
        {
            "cart_items": cart_items,
            "addresses": addresses,
            "total": total,
            "discount_amount": discount_amount,
            "final_total": final_total,
            "coupon_code": coupon_code,
        },
    )


# ============================================================
# APPLY COUPON
# ============================================================

@login_required
def apply_coupon(request):

    if request.method != "POST":

        return redirect("checkout")

    code = request.POST.get(
        "coupon",
        ""
    ).strip().upper()

    # ========================================================
    # FIND COUPON
    # ========================================================

    try:

        coupon = Coupon.objects.get(
            code=code
        )

    except Coupon.DoesNotExist:

        messages.error(
            request,
            "Invalid coupon code."
        )

        return redirect("checkout")

    # ========================================================
    # CHECK COUPON VALIDITY
    # ========================================================

    if not coupon.is_valid():

        messages.error(
            request,
            "This coupon is expired or inactive."
        )

        return redirect("checkout")

    # ========================================================
    # CALCULATE CART TOTAL
    # ========================================================

    cart = request.session.get(
        "cart",
        {}
    )

    total = 0

    for product_id, quantity in cart.items():

        try:

            product = Product.objects.get(
                id=product_id
            )

        except Product.DoesNotExist:

            continue

        total += (
            product.discount_price * quantity
        )

    # ========================================================
    # MINIMUM ORDER AMOUNT
    # ========================================================

    if total < coupon.minimum_amount:

        messages.error(
            request,
            f"Minimum order amount for this coupon "
            f"is ₹{coupon.minimum_amount}."
        )

        return redirect("checkout")

    # ========================================================
    # CALCULATE DISCOUNT
    # ========================================================

    discount_amount = (
        total * coupon.discount / 100
    )

    final_total = (
        total - discount_amount
    )

    # ========================================================
    # SAVE COUPON IN SESSION
    # ========================================================

    request.session["coupon_code"] = (
        coupon.code
    )

    request.session["discount_amount"] = (
        float(discount_amount)
    )

    request.session["final_total"] = (
        float(final_total)
    )

    messages.success(
        request,
        f"Coupon {coupon.code} applied successfully!"
    )

    return redirect("checkout")


# ============================================================
# MY ORDERS
# ============================================================

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "my_orders.html",
        {
            "orders": orders,
        },
    )


# ============================================================
# ADMIN ORDERS
# ============================================================

@user_passes_test(is_admin)
def admin_orders(request):

    orders = Order.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_orders.html",
        {
            "orders": orders,
        },
    )


# ============================================================
# ORDER DETAIL
# ============================================================

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        "order_detail.html",
        {
            "order": order,
        },
    )


# ============================================================
# CANCEL ORDER
# ============================================================

@login_required
def cancel_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    if order.order_status in [
        "Pending",
        "Confirmed"
    ]:

        order.order_status = "Cancelled"

        order.save()

        # ====================================================
        # RESTORE PRODUCT STOCK
        # ====================================================

        for item in order.items.all():

            product = item.product

            product.stock += item.quantity

            product.is_available = True

            product.save()

        messages.success(
            request,
            "Order cancelled successfully "
            "and product stock has been restored."
        )

    else:

        messages.error(
            request,
            "This order cannot be cancelled."
        )

    return redirect("orders")


# ============================================================
# DOWNLOAD INVOICE
# ============================================================

@login_required
def download_invoice(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="Invoice_Order_{order.id}.pdf"'
    )

    pdf = canvas.Canvas(response)

    y = 800

    # ========================================================
    # COMPANY
    # ========================================================

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawString(
        50,
        y,
        "Enterprise Ecommerce Invoice"
    )

    y -= 40

    pdf.setFont(
        "Helvetica",
        12
    )

    # ========================================================
    # ORDER INFORMATION
    # ========================================================

    pdf.drawString(
        50,
        y,
        f"Order ID : #{order.id}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Date : {order.created_at}"
    )

    y -= 20

    customer_name = (
        order.user.get_full_name()
        or order.user.username
    )

    pdf.drawString(
        50,
        y,
        f"Customer : {customer_name}"
    )

    y -= 30

    # ========================================================
    # SHIPPING ADDRESS
    # ========================================================

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Shipping Address"
    )

    y -= 20

    pdf.setFont(
        "Helvetica",
        12
    )

    if order.address:

        pdf.drawString(
            70,
            y,
            order.address.full_name
        )

        y -= 20

        pdf.drawString(
            70,
            y,
            order.address.address
        )

        y -= 20

        pdf.drawString(
            70,
            y,
            f"{order.address.city}, "
            f"{order.address.state}"
        )

        y -= 20

        pdf.drawString(
            70,
            y,
            f"{order.address.country} - "
            f"{order.address.pincode}"
        )

    y -= 40

    # ========================================================
    # ORDERED PRODUCTS
    # ========================================================

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Ordered Products"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        12
    )

    for item in order.items.all():

        pdf.drawString(
            60,
            y,
            item.product.name
        )

        pdf.drawString(
            280,
            y,
            f"Qty : {item.quantity}"
        )

        pdf.drawString(
            400,
            y,
            f"₹{item.price}"
        )

        y -= 20

        if y < 80:

            pdf.showPage()

            y = 800

            pdf.setFont(
                "Helvetica",
                12
            )

    y -= 20

    # ========================================================
    # TOTAL
    # ========================================================

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        f"Total : ₹{order.total_price}"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        12
    )

    # ========================================================
    # PAYMENT INFORMATION
    # ========================================================

    pdf.drawString(
        50,
        y,
        f"Payment Method : "
        f"{order.payment_method}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Payment Status : "
        f"{order.payment_status}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Order Status : "
        f"{order.order_status}"
    )

    pdf.showPage()

    pdf.save()

    return response


# ============================================================
# RAZORPAY PAYMENT SUCCESS
# ============================================================

@login_required
def payment_success(request):

    payment_id = request.GET.get(
        "payment_id"
    )

    order_id = request.GET.get(
        "order_id"
    )

    signature = request.GET.get(
        "signature"
    )

    # ========================================================
    # VALIDATE REQUIRED PAYMENT DATA
    # ========================================================

    if not payment_id or not order_id or not signature:

        messages.error(
            request,
            "Invalid payment response."
        )

        return redirect("orders")

    # ========================================================
    # FIND USER'S ORDER
    # ========================================================

    order = get_object_or_404(
        Order,
        razorpay_order_id=order_id,
        user=request.user,
    )

    # ========================================================
    # VERIFY RAZORPAY SIGNATURE
    # ========================================================

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )

    try:

        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })

    except razorpay.errors.SignatureVerificationError:

        order.payment_status = "Failed"

        order.save()

        messages.error(
            request,
            "Payment verification failed. "
            "Your payment could not be verified."
        )

        return redirect("orders")

    # ========================================================
    # PAYMENT VERIFIED SUCCESSFULLY
    # ========================================================

    order.razorpay_payment_id = payment_id

    order.payment_status = "Paid"

    order.order_status = "Confirmed"

    order.save()

    # ========================================================
    # CLEAR CART
    # ========================================================

    request.session["cart"] = {}

    # ========================================================
    # CLEAR COUPON
    # ========================================================

    request.session.pop(
        "coupon_code",
        None
    )

    request.session.pop(
        "discount_amount",
        None
    )

    request.session.pop(
        "final_total",
        None
    )

    messages.success(
        request,
        "Payment successful! "
        "Your order has been placed."
    )

    return redirect("orders")

@login_required
def admin_update_order_status(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == "POST":

        new_status = request.POST.get("order_status")

        allowed_statuses = [
            "Pending",
            "Confirmed",
            "Shipped",
            "Delivered",
            "Cancelled",
        ]

        if new_status not in allowed_statuses:

            messages.error(
                request,
                "Invalid order status."
            )

            return redirect(
                "admin_order_detail",
                order_id=order.id
            )

       
        if (
            new_status == "Cancelled"
            and order.order_status != "Cancelled"
        ):

            for item in order.items.all():

                product = item.product

                product.stock += item.quantity
                product.is_available = True

                product.save()

        order.order_status = new_status

        order.save()

        messages.success(
            request,
            f"Order #{order.id} status updated to {new_status}."
        )

    return redirect(
        "admin_order_detail",
        order_id=order.id
    )
    
# ============================================================
# ADMIN - ALL PRODUCTS
# ============================================================

@login_required
def admin_products(request):

    products = Product.objects.all().order_by("-id")

    # Search by product name or brand
    search = request.GET.get("search", "").strip()

    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
        )

    # Category filter
    category_id = request.GET.get("category")

    if category_id:
        products = products.filter(
            category_id=category_id
        )

    # Availability filter
    availability = request.GET.get("availability")

    if availability == "available":

        products = products.filter(
            is_available=True,
            stock__gt=0
        )

    elif availability == "out_of_stock":

        products = products.filter(
            stock=0
        )

    categories = Category.objects.all()

    return render(
        request,
        "admin_products.html",
        {
            "products": products,
            "categories": categories,
            "search": search,
            "selected_category": category_id,
            "availability": availability,
        },
    )
# ============================================================
# ADMIN - ADD PRODUCT
# ============================================================

@login_required
def admin_add_product(request):

    if request.method == "POST":

        name = request.POST.get("name")
        brand = request.POST.get("brand")
        category_id = request.POST.get("category")
        price = request.POST.get("price")
        discount_price = request.POST.get("discount_price")
        stock = request.POST.get("stock")
        description = request.POST.get("description")
        is_available = request.POST.get("is_available") == "on"

        category = get_object_or_404(
            Category,
            id=category_id
        )

        Product.objects.create(
            name=name,
            brand=brand,
            category=category,
            price=price,
            discount_price=discount_price,
            stock=stock,
            description=description,
            is_available=is_available,
        )

        messages.success(
            request,
            "Product added successfully!"
        )

        return redirect("admin_products")

    categories = Category.objects.all()

    return render(
        request,
        "admin_add_product.html",
        {
            "categories": categories,
        },
    )
    
# ============================================================
# ADMIN - EDIT PRODUCT
# ============================================================

@login_required
def admin_edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.name = request.POST.get("name")
        product.brand = request.POST.get("brand")

        category_id = request.POST.get("category")

        product.category = get_object_or_404(
            Category,
            id=category_id
        )

        product.price = request.POST.get("price")
        product.discount_price = request.POST.get(
            "discount_price"
        )
        product.stock = request.POST.get("stock")
        product.description = request.POST.get(
            "description"
        )

        product.is_available = (
            request.POST.get("is_available") == "on"
        )

        product.save()

        messages.success(
            request,
            "Product updated successfully!"
        )

        return redirect("admin_products")

    categories = Category.objects.all()

    return render(
        request,
        "admin_edit_product.html",
        {
            "product": product,
            "categories": categories,
        },
    )
    
# ============================================================
# ADMIN - DELETE PRODUCT
# ============================================================

@login_required
def admin_delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.delete()

        messages.success(
            request,
            "Product deleted successfully!"
        )

    return redirect("admin_products")

# ============================================================
# ADMIN - DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):

    from orders.models import Order

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_customers = (
        Order.objects.values("user").distinct().count()
    )

    total_sales = 0

    paid_orders = Order.objects.filter(
        payment_status="Paid"
    )

    for order in paid_orders:
        total_sales += order.total_price

    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=5
    ).order_by("stock")

    out_of_stock_products = Product.objects.filter(
        stock=0
    )

    recent_orders = Order.objects.select_related(
        "user"
    ).order_by(
        "-created_at"
    )[:10]

    return render(
        request,
        "admin_dashboard.html",
        {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_sales": total_sales,
            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "recent_orders": recent_orders,
        },
    )