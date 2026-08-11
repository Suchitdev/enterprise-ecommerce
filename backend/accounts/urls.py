from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),

    path("addresses/", views.addresses, name="addresses"),
    path("add-address/", views.add_address, name="add_address"),
    path("addresses/edit/<int:id>/", views.edit_address, name="edit_address"),
    path("addresses/delete/<int:id>/", views.delete_address, name="delete_address"),
]