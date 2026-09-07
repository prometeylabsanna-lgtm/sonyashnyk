from django.urls import path

from . import views

app_name = "orders_cart"

urlpatterns = [
    path("", views.cart_page, name="page"),
    path("shtorka/", views.cart_drawer_partial, name="drawer"),
    path("dodaty/", views.cart_add, name="add"),
    path("onovyty/<int:variant_id>/", views.cart_update, name="update"),
    path("vydalyty/<int:variant_id>/", views.cart_remove, name="remove"),
]
