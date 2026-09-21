from django.shortcuts import render

from apps.core.db_safe import database_reachable
from apps.core.pickup_points import get_pickup_points

from .models import Certificate


def about(request):
    return render(request, "pages/about.html")


def delivery(request):
    return render(request, "pages/delivery.html")


def certificates(request):
    if not database_reachable():
        items = []
        series_list = []
    else:
        items = Certificate.objects.filter(is_active=True).select_related("product")
        series_list = sorted({c.series for c in items if c.series})
    return render(
        request,
        "pages/certificates.html",
        {"certificates": items, "series_list": series_list},
    )


def contacts(request):
    return render(request, "pages/contacts.html", {"pickup_points": get_pickup_points()})


def offer(request):
    return render(request, "pages/offer.html")


def privacy(request):
    return render(request, "pages/privacy.html")
