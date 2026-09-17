from django.conf import settings

from apps.core.admin_site_content import SITE_BLOCKS_CACHE_KEY
from apps.core.db_safe import database_reachable
from apps.core.i18n_utils import pick
from apps.core.models import SiteSettings


def _load_site_blocks():
    from django.core.cache import cache

    from apps.core.models import SiteBlock

    cached = cache.get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached
    data = {b.cache_key: b for b in SiteBlock.objects.all()}
    cache.set(SITE_BLOCKS_CACHE_KEY, data, 60)
    return data


def site_settings(request):
    """Глобальні дані сайту + CMS-блоки для шаблонів."""
    site_name = getattr(settings, "SITE_NAME", "Соняшник")
    site_phone = getattr(settings, "SITE_PHONE", "")
    site_phone_raw = getattr(settings, "SITE_PHONE_RAW", "")
    site_working_hours = getattr(settings, "SITE_WORKING_HOURS", "")
    free_shipping_threshold = getattr(settings, "FREE_SHIPPING_THRESHOLD", 1500)
    site_email = ""
    site_address = ""
    instagram_url = tiktok_url = telegram_url = ""
    site_blocks = {}

    if database_reachable():
        solo = SiteSettings.get_solo()
        site_name = solo.site_name or site_name
        site_phone = solo.phone or site_phone
        site_phone_raw = solo.phone_raw or site_phone_raw
        site_working_hours = pick(solo.work_hours, getattr(solo, "work_hours_ru", "")) or site_working_hours
        free_shipping_threshold = solo.free_shipping_threshold or free_shipping_threshold
        site_email = solo.email
        site_address = pick(solo.address, getattr(solo, "address_ru", ""))
        instagram_url = solo.instagram_url
        tiktok_url = solo.tiktok_url
        telegram_url = solo.telegram_url
        try:
            site_blocks = _load_site_blocks()
        except Exception:
            site_blocks = {}

    return {
        "site_name": site_name,
        "site_phone": site_phone,
        "site_phone_raw": site_phone_raw,
        "site_working_hours": site_working_hours,
        "site_email": site_email,
        "site_address": site_address,
        "free_shipping_threshold": free_shipping_threshold,
        "site_instagram_url": instagram_url,
        "site_tiktok_url": tiktok_url,
        "site_telegram_url": telegram_url,
        "site_blocks": site_blocks,
    }
