import razorpay
from django.conf import settings
from django.shortcuts import render


def payment_page(request):

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    amount = 50000  # ₹500 (amount in paise)

    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount,
    }

    return render(request, "payment.html", context)