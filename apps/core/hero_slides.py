"""HeroSlide service: seed + frontend fallback на static."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.core.i18n_utils import normalize_lang
from apps.core.models import HeroSlide

DEFAULT_HERO_SLIDES = (
    {
        "title": "Якісне насіння для багатого врожаю",
        "title_ru": "Качественные семена для богатого урожая",
        "lead": "Овочеве, квіткове та вагове насіння з перевіреною схожістю — для саду, городу й розсади.",
        "lead_ru": "Овощные, цветочные и весовые семена с проверенной всхожестью — для сада, огорода и рассады.",
        "cta1_text": "До каталогу",
        "cta1_text_ru": "В каталог",
        "cta1_url": "/katalog/nasinnia/",
        "cta2_text": "До акцій",
        "cta2_text_ru": "К акциям",
        "cta2_url": "/katalog/aktsiyi/",
        "static_image": "img/home/hero-seeds.webp",
        "order": 0,
    },
    {
        "title": "Овочі з вашої ділянки",
        "title_ru": "Овощи с вашего участка",
        "lead": "Насіння овочевих культур для свіжих салатів, консервації та сімейного столу весь сезон.",
        "lead_ru": "Семена овощных культур для свежих салатов, консервации и семейного стола весь сезон.",
        "cta1_text": "Обрати насіння",
        "cta1_text_ru": "Выбрать семена",
        "cta1_url": "/katalog/nasinnia/",
        "cta2_text": "До акцій",
        "cta2_text_ru": "К акциям",
        "cta2_url": "/katalog/aktsiyi/",
        "static_image": "img/home/hero-vegetables.webp",
        "order": 1,
    },
    {
        "title": "Добрива для сильного росту",
        "title_ru": "Удобрения для сильного роста",
        "lead": "Органічні та мінеральні підживлення з перевіреною якістю — для здорових рослин і високого врожаю.",
        "lead_ru": "Органические и минеральные подкормки с проверенным качеством — для здоровых растений и высокого урожая.",
        "cta1_text": "До добрив",
        "cta1_text_ru": "К удобрениям",
        "cta1_url": "/katalog/dobriva-ta-stimuliatori-rostu/",
        "cta2_text": "До акцій",
        "cta2_text_ru": "К акциям",
        "cta2_url": "/katalog/aktsiyi/",
        "static_image": "img/home/hero-fertilizer.webp",
        "order": 2,
    },
)


@dataclass
class HeroSlideView:
    title: str
    lead: str
    eyebrow: str
    cta1_text: str
    cta1_url: str
    cta2_text: str
    cta2_url: str
    image_url: str | None
    static_image: str | None
    alt_text: str


def _pick(lang: str, uk: str | None, ru: str | None) -> str:
    uk_val = uk or ""
    ru_val = (ru or "").strip()
    if lang == "ru" and ru_val:
        return ru_val
    return uk_val


def ensure_default_hero_slides() -> int:
    if HeroSlide.objects.exists():
        return 0
    created = 0
    for item in DEFAULT_HERO_SLIDES:
        HeroSlide.objects.create(
            title=item["title"],
            title_ru=item.get("title_ru", ""),
            lead=item["lead"],
            lead_ru=item.get("lead_ru", ""),
            cta1_text=item["cta1_text"],
            cta1_text_ru=item.get("cta1_text_ru", ""),
            cta1_url=item["cta1_url"],
            cta2_text=item["cta2_text"],
            cta2_text_ru=item.get("cta2_text_ru", ""),
            cta2_url=item["cta2_url"],
            order=item["order"],
            is_active=True,
            alt_text=item["title"],
            alt_text_ru=item.get("title_ru", ""),
        )
        created += 1
    return created


_DEFAULT_BY_TITLE = {item["title"]: item for item in DEFAULT_HERO_SLIDES}


def _fallback_for(slide: HeroSlide, idx: int) -> dict | None:
    by_title = _DEFAULT_BY_TITLE.get(slide.title or "")
    if by_title:
        return by_title
    if idx < len(DEFAULT_HERO_SLIDES):
        return DEFAULT_HERO_SLIDES[idx]
    return None


def _static_slides(lang: str) -> list[HeroSlideView]:
    return [
        HeroSlideView(
            title=_pick(lang, item["title"], item.get("title_ru")),
            lead=_pick(lang, item["lead"], item.get("lead_ru")),
            eyebrow="",
            cta1_text=_pick(lang, item["cta1_text"], item.get("cta1_text_ru")),
            cta1_url=item["cta1_url"],
            cta2_text=_pick(lang, item["cta2_text"], item.get("cta2_text_ru")),
            cta2_url=item["cta2_url"],
            image_url=None,
            static_image=item["static_image"],
            alt_text=_pick(lang, item["title"], item.get("title_ru")),
        )
        for item in DEFAULT_HERO_SLIDES
    ]


def get_hero_slides(lang: str | None = None) -> list[HeroSlideView]:
    from django.db.utils import OperationalError, ProgrammingError

    from apps.core.db_safe import database_reachable, reset_database_reachable_cache
    from apps.core.i18n_utils import current_lang

    lang = normalize_lang(lang or current_lang())
    if not database_reachable():
        return _static_slides(lang)

    try:
        qs = list(HeroSlide.objects.filter(is_active=True).order_by("order", "id"))
    except (OperationalError, ProgrammingError):
        reset_database_reachable_cache()
        return _static_slides(lang)

    if not qs:
        return _static_slides(lang)

    result: list[HeroSlideView] = []
    for idx, slide in enumerate(qs):
        fallback = _fallback_for(slide, idx)
        static = None
        if not slide.image and fallback:
            static = fallback["static_image"]
        image_url = None
        if slide.image:
            try:
                image_url = slide.image.url
            except Exception:
                image_url = None

        title_ru = (slide.title_ru or "").strip() or (
            fallback.get("title_ru", "") if fallback else ""
        )
        lead_ru = (slide.lead_ru or "").strip() or (
            fallback.get("lead_ru", "") if fallback else ""
        )
        cta1_ru = (slide.cta1_text_ru or "").strip() or (
            fallback.get("cta1_text_ru", "") if fallback else ""
        )
        cta2_ru = (slide.cta2_text_ru or "").strip() or (
            fallback.get("cta2_text_ru", "") if fallback else ""
        )
        alt_ru = (slide.alt_text_ru or "").strip() or title_ru

        title = _pick(lang, slide.title, title_ru)
        result.append(
            HeroSlideView(
                title=title,
                lead=_pick(lang, slide.lead, lead_ru),
                eyebrow=_pick(lang, slide.eyebrow, slide.eyebrow_ru),
                cta1_text=_pick(lang, slide.cta1_text, cta1_ru),
                cta1_url=slide.cta1_url,
                cta2_text=_pick(lang, slide.cta2_text, cta2_ru),
                cta2_url=slide.cta2_url,
                image_url=image_url,
                static_image=static,
                alt_text=_pick(lang, slide.alt_text, alt_ru) or title,
            )
        )
    return result


def static_url(path: str) -> str:
    return f"{settings.STATIC_URL}{path.lstrip('/')}"
