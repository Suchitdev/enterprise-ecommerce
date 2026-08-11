from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_price",
        "order_status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "order_status",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "id",
        "user__username",
        "user__email",
    )

    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount",
        "minimum_amount",
        "valid_from",
        "valid_to",
        "active",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "code",
    )