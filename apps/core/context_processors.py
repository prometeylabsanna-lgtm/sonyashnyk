from django.conf import settings

from .db_safe import database_reachable
from .models import SiteSettings


def site_settings(request):
    """Глобальні дані сайту (телефон, графік, соцмережі) для шаблонів."""
    instagram_url = tiktok_url = telegram_url = ""
    if database_reachable():
        social = SiteSettings.get_solo()
        instagram_url = social.instagram_url
        tiktok_url = social.tiktok_url
        telegram_url = social.telegram_url
    return {
        "site_name": settings.SITE_NAME,
        "site_phone": settings.SITE_PHONE,
        "site_phone_raw": settings.SITE_PHONE_RAW,
        "site_working_hours": settings.SITE_WORKING_HOURS,
        "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD,
        "site_instagram_url": instagram_url,
        "site_tiktok_url": tiktok_url,
        "site_telegram_url": telegram_url,
    }
