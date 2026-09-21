"""Точки видачі: заглушки, локалізація, віддача на сторінку контактів."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.i18n_utils import current_lang, normalize_lang
from apps.core.models import PickupPoint

PLACEHOLDER_ADDRESS = "м. Київ, адреса уточнюється"
PLACEHOLDER_ADDRESS_RU = "г. Киев, адрес уточняется"

DEFAULT_PICKUP_POINTS = tuple(
    {
        "title": f"Крамниця {index}",
        "title_ru": f"Магазин {index}",
        "address": PLACEHOLDER_ADDRESS,
        "address_ru": PLACEHOLDER_ADDRESS_RU,
        "order": index - 1,
    }
    for index in range(1, 5)
)


@dataclass(frozen=True)
class PickupPointView:
    title: str
    address: str
    phone: str
    phone_raw: str
    hours: str


def ensure_default_pickup_points() -> int:
    if PickupPoint.objects.exists():
        return 0
    created = 0
    for item in DEFAULT_PICKUP_POINTS:
        PickupPoint.objects.create(
            title=item["title"],
            title_ru=item["title_ru"],
            address=item["address"],
            address_ru=item["address_ru"],
            order=item["order"],
            is_active=True,
        )
        created += 1
    return created


def _pick(lang: str, uk: str | None, ru: str | None) -> str:
    uk_val = uk or ""
    ru_val = (ru or "").strip()
    if lang == "ru" and ru_val:
        return ru_val
    return uk_val


def _site_fallback(lang: str) -> tuple[str, str, str]:
    from apps.core.models import SiteSettings

    solo = SiteSettings.get_solo()
    return (
        solo.phone or "",
        solo.phone_raw or "",
        _pick(lang, solo.work_hours, getattr(solo, "work_hours_ru", "")),
    )


def _view_from_defaults(lang: str, phone: str, phone_raw: str, hours: str) -> list[PickupPointView]:
    return [
        PickupPointView(
            title=_pick(lang, item["title"], item["title_ru"]),
            address=_pick(lang, item["address"], item["address_ru"]),
            phone=phone,
            phone_raw=phone_raw,
            hours=hours,
        )
        for item in DEFAULT_PICKUP_POINTS
    ]


def _view_from_point(point: PickupPoint, lang: str, phone: str, phone_raw: str, hours: str) -> PickupPointView:
    own_phone = (point.phone or "").strip()
    own_raw = (point.phone_raw or "").strip()
    own_hours = _pick(lang, point.hours, point.hours_ru).strip()
    return PickupPointView(
        title=_pick(lang, point.title, point.title_ru),
        address=_pick(lang, point.address, point.address_ru),
        phone=own_phone or phone,
        phone_raw=own_raw or phone_raw,
        hours=own_hours or hours,
    )


def get_pickup_points(lang: str | None = None) -> list[PickupPointView]:
    from django.db.utils import OperationalError, ProgrammingError

    from apps.core.db_safe import database_reachable, reset_database_reachable_cache

    lang = normalize_lang(lang or current_lang())
    if not database_reachable():
        return _view_from_defaults(lang, "", "", "")

    try:
        points = list(PickupPoint.objects.filter(is_active=True).order_by("order", "id"))
        phone, phone_raw, hours = _site_fallback(lang)
    except (OperationalError, ProgrammingError):
        reset_database_reachable_cache()
        return _view_from_defaults(lang, "", "", "")

    if not points:
        return _view_from_defaults(lang, phone, phone_raw, hours)
    return [_view_from_point(point, lang, phone, phone_raw, hours) for point in points]
