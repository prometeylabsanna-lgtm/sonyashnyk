from django.conf import settings


def site_settings(request):
    """Глобальні дані сайту (телефон, графік роботи тощо) для шаблонів."""
    return {
        "site_name": settings.SITE_NAME,
        "site_phone": settings.SITE_PHONE,
        "site_phone_raw": settings.SITE_PHONE_RAW,
        "site_working_hours": settings.SITE_WORKING_HOURS,
        "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD,
    }
