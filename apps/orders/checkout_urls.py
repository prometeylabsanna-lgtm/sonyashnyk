from django.urls import path

from . import views

app_name = "orders_checkout"

urlpatterns = [
    path("", views.checkout, name="page"),
    path("dyakuyemo/<str:order_number>/", views.thank_you, name="thank_you"),
    path("oplata/<str:order_number>/", views.pay, name="pay"),
    path("oplata/<str:order_number>/mock/", views.pay_mock, name="pay_mock"),
    path("liqpay/callback/", views.liqpay_callback, name="liqpay_callback"),
    path("np/mista/", views.np_cities, name="np_cities"),
    path("np/viddilennya/", views.np_warehouses, name="np_warehouses"),
]
