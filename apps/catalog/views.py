from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .category_tree import HOME_ROOT_SLUGS
from .filters import apply_sorting, build_filter_context, filter_products
from .models import Category, Product

PRODUCTS_PER_PAGE = 12


def _paginate(request, products):
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    return paginator.get_page(page_number)


def catalog_index(request):
    """Корінь каталогу /katalog/ — плитки категорій 1 рівня + сітка товарів."""
    cats_by_slug = {
        c.slug: c
        for c in Category.objects.filter(
            slug__in=HOME_ROOT_SLUGS, parent__isnull=True, is_active=True
        )
    }
    root_categories = [cats_by_slug[s] for s in HOME_ROOT_SLUGS if s in cats_by_slug]
    products = Product.objects.filter(is_active=True).prefetch_related("variants", "images")
    products = filter_products(request, products)
    products = apply_sorting(request, products)

    context = {
        "category": None,
        "is_catalog_root": True,
        "breadcrumbs": [],
        "subcategories": root_categories,
        "products": _paginate(request, products),
        "total_count": products.count(),
        "current_sort": request.GET.get("sort", "popularity"),
        **build_filter_context(request, products),
    }
    return render(request, "catalog/category.html", context)


def category(request, slug):
    """Сторінка категорії: плитки підкатегорій (якщо є) + сітка товарів + фільтри."""
    current_category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = current_category.children.filter(is_active=True).order_by("order", "name")

    descendant_ids = current_category.get_descendant_ids()
    products = Product.objects.filter(category_id__in=descendant_ids, is_active=True).prefetch_related(
        "variants", "images"
    )
    products = filter_products(request, products)
    products = apply_sorting(request, products)

    context = {
        "category": current_category,
        "breadcrumbs": current_category.breadcrumb_chain(),
        "subcategories": subcategories,
        "products": _paginate(request, products),
        "total_count": products.count(),
        "current_sort": request.GET.get("sort", "popularity"),
        **build_filter_context(request, products),
    }
    return render(request, "catalog/category.html", context)


def sale(request):
    """Віртуальна категорія «Акції / знижки» — товари з is_sale=True."""
    products = Product.objects.filter(is_active=True, is_sale=True).prefetch_related("variants", "images")
    products = filter_products(request, products)
    products = apply_sorting(request, products)

    context = {
        "category": None,
        "is_sale_page": True,
        "breadcrumbs": [],
        "subcategories": [],
        "products": _paginate(request, products),
        "total_count": products.count(),
        "current_sort": request.GET.get("sort", "popularity"),
        **build_filter_context(request, products),
    }
    return render(request, "catalog/category.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("variants", "images", "certificates"),
        slug=slug, is_active=True,
    )
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .prefetch_related("variants", "images")[:8]
    )
    context = {
        "product": product,
        "breadcrumbs": product.category.breadcrumb_chain(),
        "related_products": related_products,
    }
    return render(request, "catalog/product_detail.html", context)


def search(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(short_description__icontains=query),
            is_active=True,
        ).prefetch_related("variants", "images")
        products = apply_sorting(request, products)

    context = {
        "query": query,
        "products": _paginate(request, products) if query else None,
        "total_count": products.count() if query else 0,
    }
    return render(request, "catalog/search.html", context)


def wishlist(request):
    """Сторінка «Обране» — товари підвантажуються з localStorage через fragment."""
    return render(request, "catalog/wishlist.html")


def wishlist_fragment(request):
    """HTML-фрагмент карток для обраного. ?ids=1,2,3"""
    raw = request.GET.get("ids", "")
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        pk = int(part)
        if pk > 0 and pk not in ids:
            ids.append(pk)
        if len(ids) >= 60:
            break

    products = []
    if ids:
        qs = (
            Product.objects.filter(pk__in=ids, is_active=True)
            .prefetch_related("variants", "images", "category")
        )
        by_id = {p.pk: p for p in qs}
        products = [by_id[i] for i in ids if i in by_id]

    return render(request, "catalog/wishlist_fragment.html", {"products": products})
