from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import OrderItem
from .models import Review
from .models import Product, Category


# ==========================
# Home Page
# ==========================
def home(request):

    query = request.GET.get("q")
    category_slug = request.GET.get("category")
    brand = request.GET.get("brand")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    sort = request.GET.get("sort")

    products = Product.objects.filter(is_available=True)

    # Search
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category Filter
    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    # Brand Filter
    if brand:
        products = products.filter(
            brand__iexact=brand
        )

    # Min Price
    if min_price:
        products = products.filter(
            discount_price__gte=min_price
        )

    # Max Price
    if max_price:
        products = products.filter(
            discount_price__lte=max_price
        )

    # Sorting
    if sort == "price_low":
        products = products.order_by("discount_price")

    elif sort == "price_high":
        products = products.order_by("-discount_price")

    elif sort == "name":
        products = products.order_by("name")

    elif sort == "newest":
        products = products.order_by("-created_at")

    categories = Category.objects.all()

    brands = Product.objects.values_list(
        "brand",
        flat=True
    ).distinct()

    paginator = Paginator(products, 6)

    page_number = request.GET.get("page")

    products = paginator.get_page(page_number)

    context = {
        "products": products,
        "categories": categories,
        "brands": brands,

        "query": query,
        "selected_category": category_slug,
        "selected_brand": brand,

        "min_price": min_price,
        "max_price": max_price,

        "sort": sort,
    }

    return render(
        request,
        "home.html",
        context
    )


# ==========================
# Product Detail
# ==========================
def product_detail(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug
    )

    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(
        id=product.id
    )[:4]

    context = {
        "product": product,
        "related_products": related_products,
    }

    return render(
        request,
        "product_detail.html",
        context
    )


# ==========================
# Cart
# ==========================
def add_to_cart(request, slug):

    product = get_object_or_404(Product, slug=slug)

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session["cart"] = cart

    return redirect("cart")


def remove_from_cart(request, slug):

    product = get_object_or_404(Product, slug=slug)

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:
        del cart[product_id]

    request.session["cart"] = cart

    return redirect("cart")


def increase_quantity(request, slug):

    product = get_object_or_404(Product, slug=slug)

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:
        cart[product_id] += 1

    request.session["cart"] = cart

    return redirect("cart")


def decrease_quantity(request, slug):

    product = get_object_or_404(Product, slug=slug)

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    request.session["cart"] = cart

    return redirect("cart")


def cart(request):

    cart = request.session.get("cart", {})

    cart_items = []

    total = 0

    for product_id, quantity in cart.items():

        product = Product.objects.get(id=product_id)

        subtotal = product.discount_price * quantity

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(
        request,
        "cart.html",
        context
    )


# ==========================
# Wishlist
# ==========================
def wishlist(request):

    wishlist = request.session.get("wishlist", [])

    products = Product.objects.filter(
        slug__in=wishlist
    )

    return render(
        request,
        "wishlist.html",
        {
            "products": products,
        }
    )


def add_to_wishlist(request, slug):

    wishlist = request.session.get("wishlist", [])

    if slug not in wishlist:
        wishlist.append(slug)

    request.session["wishlist"] = wishlist

    return redirect("wishlist")


def remove_from_wishlist(request, slug):

    wishlist = request.session.get("wishlist", [])

    if slug in wishlist:
        wishlist.remove(slug)

    request.session["wishlist"] = wishlist

    return redirect("wishlist")

@login_required
def add_review(request, slug):

    product = get_object_or_404(Product, slug=slug)

    purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
    ).exists()

    if not purchased:

        messages.error(
            request,
            "You can review only purchased products."
        )

        return redirect("product_detail", slug=slug)

    if request.method == "POST":

        rating = request.POST.get("rating")
        review = request.POST.get("review")

        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            review=review,
        )

        messages.success(
            request,
            "Review Submitted Successfully."
        )

    return redirect("product_detail", slug=slug)