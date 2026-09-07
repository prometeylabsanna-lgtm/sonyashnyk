from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.catalog import views as catalog_views
from apps.core import views as core_views
from apps.pages import views as pages_views

from .sitemaps import CategorySitemap, ProductSitemap

sitemaps = {"products": ProductSitemap, "categories": CategorySitemap}

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", core_views.home, name="home"),

    path("katalog/", include("apps.catalog.urls")),
    path("tovar/<slug:slug>/", catalog_views.product_detail, name="product_detail"),
    path("poshuk/", catalog_views.search, name="search"),

    path("koshyk/", include("apps.orders.cart_urls")),
    path("oformlennya/", include("apps.orders.checkout_urls")),

    path("zayavka/", include("apps.leads.urls")),

    path("pro-nas/", pages_views.about, name="about"),
    path("dostavka-i-oplata/", pages_views.delivery, name="delivery"),
    path("sertyfikaty/", pages_views.certificates, name="certificates"),
    path("kontakty/", pages_views.contacts, name="contacts"),
    path("oferta/", pages_views.offer, name="offer"),
    path("privacy/", pages_views.privacy, name="privacy"),

    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

handler404 = "apps.core.views.custom_404"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
