from django.urls import path

from . import views

app_name = "orders_checkout"

urlpatterns = [
    path("", views.checkout, name="page"),
    path("dyakuyemo/<str:order_number>/", views.thank_you, name="thank_you"),
]
