from django.db import models
from django.conf import settings
from products.models import Product
from accounts.models import Address
from django.utils import timezone


class Order(models.Model):

    ORDER_STATUS = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Shipped", "Shipped"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    PAYMENT_METHODS = [
        ("COD", "Cash on Delivery"),
        ("ONLINE", "Online Payment"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="COD"
    )

    # ==========================
    # Razorpay Fields
    # ==========================

    razorpay_order_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    razorpay_payment_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    razorpay_signature = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    order_status = models.CharField(
        max_length=30,
        choices=ORDER_STATUS,
        default="Pending"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name


# ==========================
# Coupon Model
# ==========================

class Coupon(models.Model):

    code = models.CharField(
        max_length=30,
        unique=True
    )

    discount = models.PositiveIntegerField(
        help_text="Percentage Discount"
    )

    minimum_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    valid_from = models.DateTimeField()

    valid_to = models.DateTimeField()

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def is_valid(self):
        now = timezone.now()

        return (
            self.active and
            self.valid_from <= now <= self.valid_to
        )

    def __str__(self):
        return self.code