from django.shortcuts import render

from apps.catalog.category_tree import HOME_ROOT_SLUGS
from apps.catalog.models import Category, Product

from .models import HeroSlide, HighlightPoint, Review

# Іконки категорій (static WebP з прозорим фоном) — не змінюємо набір головної
CATEGORY_ICONS = {
    "nasinnia": "img/home/categories/nasinnya.webp",
    "dobriva-ta-stimuliatori-rostu": "img/home/categories/dobryva.webp",
    "zasobi-zakhistu-roslin": "img/home/categories/zakhyst.webp",
    "sadovii-instrument": "img/home/categories/polyv.webp",
    "poliv-ta-opriskuvachi": "img/home/categories/polyv.webp",
    "posadkovii-material": "img/home/categories/posadkovyi.webp",
    "gorshchiki": "img/home/categories/gorshchyky.webp",
    "grunti-ta-vse-dlia-posadki": "img/home/categories/grunty.webp",
}
CATEGORY_ICON_FALLBACK = "img/home/categories/nasinnya.webp"


def home(request):
    # Фіксований набір кореневих плиток на головній (нові корені не змішуємо)
    cats_by_slug = {
        c.slug: c
        for c in Category.objects.filter(slug__in=HOME_ROOT_SLUGS, parent__isnull=True, is_active=True)
    }
    top_categories = [cats_by_slug[s] for s in HOME_ROOT_SLUGS if s in cats_by_slug]
    for cat in top_categories:
        cat.icon_static = CATEGORY_ICONS.get(cat.slug, CATEGORY_ICON_FALLBACK)

    reviews_qs = list(Review.objects.filter(is_active=True)[:5])
    featured_review = reviews_qs[0] if reviews_qs else None
    side_reviews = reviews_qs[1:5] if reviews_qs else []

    context = {
        "slides": HeroSlide.objects.filter(is_active=True),
        "trust_points": HighlightPoint.objects.filter(is_active=True, section=HighlightPoint.Section.TRUST),
        "info_points": HighlightPoint.objects.filter(is_active=True, section=HighlightPoint.Section.INFO),
        "top_categories": top_categories,
        "hit_products": Product.objects.filter(is_active=True, is_hit=True).prefetch_related("variants", "images")[:8],
        "new_products": Product.objects.filter(is_active=True, is_new=True).prefetch_related("variants", "images")[:8],
        "sale_products": Product.objects.filter(is_active=True, is_sale=True).prefetch_related("variants", "images")[:4],
        "reviews": reviews_qs,
        "featured_review": featured_review,
        "side_reviews": side_reviews,
    }
    return render(request, "core/home.html", context)


def custom_404(request, exception=None):
    return render(request, "404.html", status=404)
