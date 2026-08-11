from django.urls import path
from . import views

urlpatterns = [

    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    path(
        "orders/",
        views.my_orders,
        name="orders",
    ),

    path(
        "orders/cancel/<int:order_id>/",
        views.cancel_order,
        name="cancel_order",
    ),
    
    path(
    "orders/<int:order_id>/",
    views.order_detail,
    name="order_detail",
    ),
    
    path(
    "invoice/<int:order_id>/",
    views.download_invoice,
    name="download_invoice",
    ),
    
    path(
    "payment-success/",
    views.payment_success,
    name="payment_success",
    ),
    
    path(
    "apply-coupon/",
    views.apply_coupon,
    name="apply_coupon",
    ),
    
    path(
    "admin-orders/",
    views.admin_orders,
    name="admin_orders",
    ),
    
    path(
    "admin/orders/<int:order_id>/status/",
    views.admin_update_order_status,
    name="admin_update_order_status",
    ),
    
    path(
    "admin/products/",
    views.admin_products,
    name="admin_products",
    ),
    
    path(
    "admin/products/add/",
    views.admin_add_product,
    name="admin_add_product",
    ),
    
    path(
    "admin/products/edit/<int:product_id>/",
    views.admin_edit_product,
    name="admin_edit_product",
    ),
    
    path(
    "admin/products/delete/<int:product_id>/",
    views.admin_delete_product,
    name="admin_delete_product",
    ),
    
    path(
    "dashboard/",
    views.admin_dashboard,
    name="admin_dashboard",
    ),
]