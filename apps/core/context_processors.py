from django.conf import settings

from .models import SiteSettings


def site_settings(request):
    """Глобальні дані сайту (телефон, графік, соцмережі) для шаблонів."""
    social = SiteSettings.get_solo()
    return {
        "site_name": settings.SITE_NAME,
        "site_phone": settings.SITE_PHONE,
        "site_phone_raw": settings.SITE_PHONE_RAW,
        "site_working_hours": settings.SITE_WORKING_HOURS,
        "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD,
        "site_instagram_url": social.instagram_url,
        "site_tiktok_url": social.tiktok_url,
        "site_telegram_url": social.telegram_url,
    }
