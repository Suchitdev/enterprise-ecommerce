from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    path("cart/", views.cart, name="cart"),
    path("add-to-cart/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<slug:slug>/", views.remove_from_cart, name="remove_from_cart"),
    path("increase/<slug:slug>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<slug:slug>/", views.decrease_quantity, name="decrease_quantity"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("add-to-wishlist/<slug:slug>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("remove-from-wishlist/<slug:slug>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("review/<slug:slug>/",views.add_review,name="add_review",),
]