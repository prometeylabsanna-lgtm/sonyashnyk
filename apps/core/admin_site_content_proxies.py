"""Реєстрація proxy CMS-секцій у Django admin."""

from unfold.admin import ModelAdmin

from apps.core import cms_proxies
from apps.core.admin_site_content import site_content_section_view
from apps.core.admin_utils import SingletonModelAdminMixin

_SECTION_MODELS = (
    (cms_proxies.HomeHeroSettings, "home", "hero"),
    (cms_proxies.HomeTrustSettings, "home", "trust"),
    (cms_proxies.HomeCategoriesSettings, "home", "categories"),
    (cms_proxies.HomeHitsSettings, "home", "hits"),
    (cms_proxies.HomeNewsSettings, "home", "news"),
    (cms_proxies.HomeStorySettings, "home", "story"),
    (cms_proxies.HomeBenefitsSettings, "home", "benefits"),
    (cms_proxies.HomeSaleSettings, "home", "sale"),
    (cms_proxies.HomeReviewsSettings, "home", "reviews"),
    (cms_proxies.SiteHeaderSettings, "site", "header"),
    (cms_proxies.SiteFooterSettings, "site", "footer"),
    (cms_proxies.SiteLeadModalSettings, "site", "lead_modal"),
    (cms_proxies.SiteFabSettings, "site", "fab"),
    (cms_proxies.AboutIntroSettings, "about", "intro"),
    (cms_proxies.AboutShelvesSettings, "about", "shelves"),
    (cms_proxies.AboutTimelineSettings, "about", "timeline"),
    (cms_proxies.AboutPhilosophySettings, "about", "philosophy"),
    (cms_proxies.AboutWhySettings, "about", "why"),
    (cms_proxies.AboutProduceSettings, "about", "produce"),
    (cms_proxies.DeliveryPageSettings, "delivery", "page"),
    (cms_proxies.CertificatesPageSettings, "certificates", "page"),
    (cms_proxies.ContactsPageSettings, "contacts", "page"),
    (cms_proxies.OfferPageSettings, "offer", "page"),
    (cms_proxies.PrivacyPageSettings, "privacy", "page"),
    (cms_proxies.CatalogPageSettings, "catalog", "page"),
    (cms_proxies.SearchPageSettings, "search", "page"),
    (cms_proxies.CartPageSettings, "cart", "page"),
    (cms_proxies.SiteCartDrawerSettings, "site", "cart_drawer"),
    (cms_proxies.CheckoutPageSettings, "checkout", "page"),
    (cms_proxies.ThankYouPageSettings, "thankyou", "page"),
    (cms_proxies.WishlistPageSettings, "wishlist", "page"),
    (cms_proxies.ProductPageSettings, "product", "page"),
    (cms_proxies.Error404Settings, "error", "page404"),
)


class SiteContentSectionAdmin(SingletonModelAdminMixin, ModelAdmin):
    page_slug: str = ""
    section_slug: str = ""

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return site_content_section_view(
            request,
            self.page_slug,
            self.section_slug,
            model_admin=self,
        )


def register_site_content_section_admins(site=None):
    from django.contrib import admin as django_admin

    admin_site = site or django_admin.site
    for model, page_slug, section_slug in _SECTION_MODELS:
        if admin_site.is_registered(model):
            continue

        admin_class = type(
            f"{model.__name__}Admin",
            (SiteContentSectionAdmin,),
            {
                "page_slug": page_slug,
                "section_slug": section_slug,
            },
        )
        admin_site.register(model, admin_class)
