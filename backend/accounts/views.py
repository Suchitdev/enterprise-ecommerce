from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Address

User = get_user_model()


# ==========================
# Register
# ==========================
def register_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        messages.success(request, "Account Created Successfully")
        return redirect("login")

    return render(request, "register.html")


# ==========================
# Login
# ==========================
def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            username=username,
            password=password,
        )

        if user:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid Credentials")

    return render(request, "login.html")


# ==========================
# Logout
# ==========================
def logout_view(request):

    logout(request)
    request.session.flush()

    messages.success(request, "Logged out successfully.")

    return redirect("home")


# ==========================
# Profile
# ==========================
@login_required
def profile(request):

    return render(request, "profile.html")


# ==========================
# Edit Profile
# ==========================
@login_required
def edit_profile(request):

    user = request.user

    if request.method == "POST":

        user.username = request.POST.get("username")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone_number = request.POST.get("phone_number", "")

        if "profile_image" in request.FILES:
            user.profile_image = request.FILES["profile_image"]

        user.save()

        messages.success(request, "Profile Updated Successfully")

        return redirect("profile")

    return render(request, "edit_profile.html")


# ==========================
# My Addresses
# ==========================
@login_required
def addresses(request):

    addresses = Address.objects.filter(user=request.user)

    return render(
        request,
        "addresses.html",
        {
            "addresses": addresses
        }
    )


# ==========================
# Add Address
# ==========================
@login_required
def add_address(request):

    if request.method == "POST":

        Address.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name"),
            phone_number=request.POST.get("phone_number"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
            country=request.POST.get("country"),
            address_type=request.POST.get("address_type"),
            is_default=request.POST.get("is_default") == "on",
        )

        messages.success(request, "Address Added Successfully.")

        return redirect("addresses")

    return render(request, "add_address.html")


# ==========================
# Edit Address
# ==========================
@login_required
def edit_address(request, id):

    address = get_object_or_404(
        Address,
        id=id,
        user=request.user
    )

    if request.method == "POST":

        address.full_name = request.POST.get("full_name")
        address.phone_number = request.POST.get("phone_number")
        address.address = request.POST.get("address")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("pincode")
        address.country = request.POST.get("country")
        address.address_type = request.POST.get("address_type")
        address.is_default = request.POST.get("is_default") == "on"

        address.save()

        messages.success(request, "Address Updated Successfully.")

        return redirect("addresses")

    return render(
        request,
        "edit_address.html",
        {
            "address": address
        }
    )


# ==========================
# Delete Address
# ==========================
@login_required
def delete_address(request, id):

    address = get_object_or_404(
        Address,
        id=id,
        user=request.user
    )

    address.delete()

    messages.success(
        request,
        "Address Deleted Successfully."
    )

    return redirect("addresses")