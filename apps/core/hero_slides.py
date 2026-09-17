"""HeroSlide service: seed + frontend fallback на static."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.core.models import HeroSlide

DEFAULT_HERO_SLIDES = (
    {
        "title": "Якісне насіння для багатого врожаю",
        "lead": "Овочеве, квіткове та вагове насіння з перевіреною схожістю — для саду, городу й розсади.",
        "cta1_text": "До каталогу",
        "cta1_url": "/katalog/nasinnia/",
        "cta2_text": "До акцій",
        "cta2_url": "/katalog/aktsiyi/",
        "static_image": "img/home/hero-seeds.webp",
        "order": 0,
    },
    {
        "title": "Овочі з вашої ділянки",
        "lead": "Насіння овочевих культур для свіжих салатів, консервації та сімейного столу весь сезон.",
        "cta1_text": "Обрати насіння",
        "cta1_url": "/katalog/nasinnia/",
        "cta2_text": "До акцій",
        "cta2_url": "/katalog/aktsiyi/",
        "static_image": "img/home/hero-vegetables.webp",
        "order": 1,
    },
    {
        "title": "Добрива для сильного росту",
        "lead": "Органічні та мінеральні підживлення з перевіреною якістю — для здорових рослин і високого врожаю.",
        "cta1_text": "До добрив",
        "cta1_url": "/katalog/dobriva-ta-stimuliatori-rostu/",
        "cta2_text": "До акцій",
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
            lead=item["lead"],
            cta1_text=item["cta1_text"],
            cta1_url=item["cta1_url"],
            cta2_text=item["cta2_text"],
            cta2_url=item["cta2_url"],
            order=item["order"],
            is_active=True,
            alt_text=item["title"],
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
            result.append(
                HeroSlideView(
                    title=slide.title,
                    lead=slide.lead,
                    eyebrow=slide.eyebrow,
                    cta1_text=slide.cta1_text,
                    cta1_url=slide.cta1_url,
                    cta2_text=slide.cta2_text,
                    cta2_url=slide.cta2_url,
                    image_url=image_url,
                    static_image=static,
                    alt_text=slide.alt_text or slide.title,
                )
            )
        return result

    return [
        HeroSlideView(
            title=item["title"],
            lead=item["lead"],
            eyebrow="",
            cta1_text=item["cta1_text"],
            cta1_url=item["cta1_url"],
            cta2_text=item["cta2_text"],
            cta2_url=item["cta2_url"],
            image_url=None,
            static_image=item["static_image"],
            alt_text=item["title"],
        )
        for item in DEFAULT_HERO_SLIDES
    ]


def static_url(path: str) -> str:
    return f"{settings.STATIC_URL}{path.lstrip('/')}"
