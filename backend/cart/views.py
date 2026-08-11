from django.shortcuts import render
from products.models import Product


def cart(request):

    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        subtotal = product.discount_price * quantity

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(
        request,
        "cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )