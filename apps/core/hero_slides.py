"""HeroSlide service: seed + frontend fallback на static."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.core.i18n_utils import loc, pick
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


def get_hero_slides() -> list[HeroSlideView]:
    qs = list(HeroSlide.objects.filter(is_active=True).order_by("order", "id"))
    if qs:
        result: list[HeroSlideView] = []
        for idx, slide in enumerate(qs):
            static = None
            if not slide.image and idx < len(DEFAULT_HERO_SLIDES):
                static = DEFAULT_HERO_SLIDES[idx]["static_image"]
            image_url = None
            if slide.image:
                try:
                    image_url = slide.image.url
                except Exception:
                    image_url = None
            title = loc(slide, "title")
            result.append(
                HeroSlideView(
                    title=title,
                    lead=loc(slide, "lead"),
                    eyebrow=loc(slide, "eyebrow"),
                    cta1_text=loc(slide, "cta1_text"),
                    cta1_url=slide.cta1_url,
                    cta2_text=loc(slide, "cta2_text"),
                    cta2_url=slide.cta2_url,
                    image_url=image_url,
                    static_image=static,
                    alt_text=pick(slide.alt_text, slide.alt_text_ru) or title,
                )
            )
        return result

    return [
        HeroSlideView(
            title=pick(item["title"], item.get("title_ru")),
            lead=pick(item["lead"], item.get("lead_ru")),
            eyebrow="",
            cta1_text=pick(item["cta1_text"], item.get("cta1_text_ru")),
            cta1_url=item["cta1_url"],
            cta2_text=pick(item["cta2_text"], item.get("cta2_text_ru")),
            cta2_url=item["cta2_url"],
            image_url=None,
            static_image=item["static_image"],
            alt_text=pick(item["title"], item.get("title_ru")),
        )
        for item in DEFAULT_HERO_SLIDES
    ]


def static_url(path: str) -> str:
    return f"{settings.STATIC_URL}{path.lstrip('/')}"
