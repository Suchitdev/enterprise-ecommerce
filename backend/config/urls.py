from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("products.urls")),
    path("", include("accounts.urls")),
    path("", include("orders.urls")),
    path("payment/", include("payments.urls")),
    path("health/", health_check, name="health_check"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )