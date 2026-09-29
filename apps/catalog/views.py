from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render

from .category_tree import HOME_ROOT_SLUGS
from .filters import annotate_card_price, apply_sorting, build_filter_context, filter_products
from .icons import attach_category_icons
from .models import Category, Product
from .search import search_products

PRODUCTS_PER_PAGE = 12


def _paginate(request, products):
    """Повертає (page_obj, page_clamped). Занадто великий page → остання сторінка."""
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    raw = request.GET.get("page", 1)
    page_clamped = False
    try:
        page_number = int(raw)
    except (TypeError, ValueError):
        page_number = 1
        page_clamped = True

    if paginator.num_pages and page_number > paginator.num_pages:
        page_clamped = True
        page_number = paginator.num_pages
    if page_number < 1:
        page_clamped = True
        page_number = 1

    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
        page_clamped = True
    return page_obj, page_clamped


def _catalog_context(request, *, products, category=None, **extra):
    base = annotate_card_price(products)
    filtered = filter_products(request, base)
    sorted_qs = apply_sorting(request, filtered)
    filter_ctx = build_filter_context(request, filtered, category=category, base_products=base)
    page_obj, page_clamped = _paginate(request, sorted_qs)
    return {
        "category": category,
        "products": page_obj,
        "page_clamped": page_clamped and filtered.exists(),
        "total_count": filtered.count(),
        "current_sort": request.GET.get("sort", "popularity"),
        "has_active_filters": filter_ctx["active_filters_count"] > 0,
        **filter_ctx,
        **extra,
    }


def catalog_index(request):
    """Корінь каталогу /katalog/ — плитки категорій 1 рівня + сітка товарів."""
    cats_by_slug = {
        c.slug: c
        for c in Category.objects.filter(
            slug__in=HOME_ROOT_SLUGS, parent__isnull=True, is_active=True
        )
    }
    root_categories = [cats_by_slug[s] for s in HOME_ROOT_SLUGS if s in cats_by_slug]
    attach_category_icons(root_categories)
    products = Product.objects.filter(is_active=True).for_cards()
    context = _catalog_context(
        request,
        products=products,
        category=None,
        is_catalog_root=True,
        breadcrumbs=[],
        subcategories=root_categories,
    )
    return render(request, "catalog/category.html", context)


def category(request, slug):
    """Сторінка категорії: плитки підкатегорій (якщо є) + сітка товарів + фільтри."""
    current_category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = list(
        current_category.children.filter(is_active=True).order_by("order", "name")
    )
    attach_category_icons(subcategories)

    descendant_ids = current_category.get_descendant_ids()
    products = Product.objects.filter(
        category_id__in=descendant_ids, is_active=True
    ).for_cards()
    context = _catalog_context(
        request,
        products=products,
        category=current_category,
        breadcrumbs=current_category.breadcrumb_chain(),
        subcategories=subcategories,
    )
    return render(request, "catalog/category.html", context)


def sale(request):
    """Віртуальна категорія «Акції / знижки» — товари з is_sale=True."""
    products = Product.objects.filter(is_active=True, is_sale=True).for_cards()
    context = _catalog_context(
        request,
        products=products,
        category=None,
        is_sale_page=True,
        breadcrumbs=[],
        subcategories=[],
    )
    return render(request, "catalog/category.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.for_cards().prefetch_related("certificates"),
        slug=slug, is_active=True,
    )
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .for_cards()[:8]
    )
    context = {
        "product": product,
        "breadcrumbs": product.category.breadcrumb_chain(),
        "related_products": related_products,
    }
    return render(request, "catalog/product_detail.html", context)


def search(request):
    raw = request.GET.get("q", "")
    base = Product.objects.filter(is_active=True).for_cards()
    products, query = search_products(base, raw)
    page_obj = None
    page_clamped = False
    total = 0
    if query:
        products = apply_sorting(request, annotate_card_price(products))
        total = products.count()
        page_obj, page_clamped = _paginate(request, products)

    context = {
        "query": query,
        "products": page_obj,
        "page_clamped": page_clamped and total > 0,
        "total_count": total,
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
            Product.objects.filter(pk__in=ids, is_active=True).for_cards()
        )
        by_id = {p.pk: p for p in qs}
        products = [by_id[i] for i in ids if i in by_id]

    return render(request, "catalog/wishlist_fragment.html", {"products": products})
