from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import render

from apps.catalog.category_tree import HOME_ROOT_SLUGS
from apps.catalog.icons import category_icon_url
from apps.catalog.models import Category, Product
from apps.core.db_safe import database_reachable, reset_database_reachable_cache
from apps.core.hero_slides import get_hero_slides
from apps.core.models import HighlightPoint, Review


def _empty_home_context(lang: str) -> dict:
    return {
        "slides": get_hero_slides(lang=lang),
        "trust_points": [],
        "info_points": [],
        "top_categories": [],
        "hit_products": [],
        "new_products": [],
        "sale_products": [],
        "reviews": [],
        "featured_review": None,
        "side_reviews": [],
    }


def home(request):
    from apps.core.i18n_utils import normalize_lang

    lang = normalize_lang(getattr(request, "LANGUAGE_CODE", None))
    if not database_reachable():
        return render(request, "core/home.html", _empty_home_context(lang))

    try:
        cats_by_slug = {
            c.slug: c
            for c in Category.objects.filter(
                slug__in=HOME_ROOT_SLUGS, parent__isnull=True, is_active=True
            )
        }
        top_categories = [cats_by_slug[s] for s in HOME_ROOT_SLUGS if s in cats_by_slug]
        for cat in top_categories:
            cat.icon_url = category_icon_url(cat)

        reviews_qs = list(Review.objects.filter(is_active=True)[:5])
        featured_review = reviews_qs[0] if reviews_qs else None
        side_reviews = reviews_qs[1:5] if reviews_qs else []

        context = {
            "slides": get_hero_slides(lang=lang),
            "trust_points": HighlightPoint.objects.filter(
                is_active=True, section=HighlightPoint.Section.TRUST
            ),
            "info_points": HighlightPoint.objects.filter(
                is_active=True, section=HighlightPoint.Section.INFO
            ),
            "top_categories": top_categories,
            "hit_products": Product.objects.filter(
                is_active=True, is_hit=True
            ).for_cards()[:8],
            "new_products": Product.objects.filter(
                is_active=True, is_new=True
            ).for_cards()[:8],
            "sale_products": Product.objects.filter(
                is_active=True, is_sale=True
            ).for_cards()[:4],
            "reviews": reviews_qs,
            "featured_review": featured_review,
            "side_reviews": side_reviews,
        }
        return render(request, "core/home.html", context)
    except (OperationalError, ProgrammingError):
        reset_database_reachable_cache()
        return render(request, "core/home.html", _empty_home_context(lang))


def custom_404(request, exception=None):
    return render(request, "404.html", status=404)
