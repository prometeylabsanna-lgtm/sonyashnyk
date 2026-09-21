"""Повне дерево категорій каталогу (до 3 рівнів).

Акції/знижки — окремий маршрут /katalog/aktsiyi/, не категорія БД.
"""

import re

# (назва, [діти...]) — дитина може бути str (лист) або (назва, [онуки])
CATEGORY_TREE = [
    (
        "Насіння",
        [
            (
                "Насіння овочів",
                [
                    "Томати",
                    "Огірки",
                    "Перці солодкі та гострі",
                    "Кабачки, цукіні, патісони",
                    "Баклажани",
                    "Буряки",
                    "Морква",
                    "Редис, редька",
                    "Салати, зелень, пряні трави",
                    "Цибуля",
                    "Горох, квасоля, боби",
                    "Капуста",
                    "Кукурудза",
                    "Гарбузи, кавуни, дині",
                ],
            ),
            (
                "Насіння квітів",
                [
                    "Однорічні",
                    "Багаторічні та дворічні",
                ],
            ),
            "Вагове насіння",
            "Газонні трави",
        ],
    ),
    (
        "Добрива та стимулятори росту",
        [
            "Добрива для газону",
            "Добрива для квітучих рослин",
            "Добрива для хвойних і вічнозелених рослин",
            "Добрива для плодово-ягідних і овочевих культур",
            "Мінеральні добрива",
            "Органічні добрива",
            "Мікробіологічні добрива та біопрепарати",
            "Біостимулятори",
            "Біодеструктори для компосту",
            "Підкислювачі та розкислювачі",
        ],
    ),
    (
        "Засоби захисту рослин",
        [
            "Фунгіциди",
            "Інсектициди",
            "Гербіциди",
            "Протруйники",
            "Біозахист від хвороб та шкідників",
            "Прилипачі та адюванти",
            "Захист від кротів, слимаків, мурах",
            "Фарба для дерев, побілка, замазка",
            "Захист від побутових шкідників",
        ],
    ),
    (
        "Садовий інструмент",
        [
            "Секатори, ножі та ножиці",
            "Сучкорізи",
            "Сокири та колуни",
            "Все для щеплення",
            "Все для газону",
            "Аксесуари",
        ],
    ),
    (
        "Полив та оприскувачі",
        [
            "Оприскувачі",
            "Запчастини та зʼєднувані",
            "Полив крапельний",
            "Шланги",
            "Розпилювачі та зрошувачі",
        ],
    ),
    (
        "Посадковий матеріал",
        [
            (
                "Цибулини та бульби квітів",
                [
                    "Тюльпани",
                    "Нарциси",
                    "Гіацинти",
                    "Крокуси",
                    "Лілії",
                    "Гладіолуси",
                    "Кали",
                    "Бегонії та глоксінії",
                    "Хости",
                    "Інші",
                ],
            ),
            (
                "Саджанці",
                [
                    "Лохина",
                    "Малина",
                    "Смородина",
                    "Аґрус",
                    "Троянди",
                    "Інші",
                    "Цибуля озима та весняна",
                    "Картопля",
                ],
            ),
        ],
    ),
    (
        "Горщики",
        [
            "Пластикові горщики",
            "Керамічні горщики",
        ],
    ),
    (
        "Грунти та все для посадки",
        [
            "Субстрати",
            "Торфи",
            "Покращувачі ґрунтів",
            "Все для розсади",
        ],
    ),
]

# Кореневі категорії, які показуємо на головній (іконки під хедером не чіпаємо)
HOME_ROOT_SLUGS = [
    "nasinnia",
    "dobriva-ta-stimuliatori-rostu",
    "zasobi-zakhistu-roslin",
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
    "posadkovii-material",
    "gorshchiki",
    "grunti-ta-vse-dlia-posadki",
]

# Порядок колонки «Категорії» у футері. Акції — окреме посилання в шаблоні.
FOOTER_CATEGORY_SLUGS = (
    "nasinnia",
    "dobriva-ta-stimuliatori-rostu",
    "zasobi-zakhistu-roslin",
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
    "zakhist-vid-pobutovikh-shkidnikiv",
    "posadkovii-material",
    "gorshchiki",
    "grunti-ta-vse-dlia-posadki",
    "vse-dlia-rozsadi",
)

# Іконки підкатегорій Насіння не перезаписуємо
SKIP_ICON_SLUGS = {
    "nasinnia",
    "nasinnia-ovochiv",
    "nasinnia-kvitiv",
    "vagove-nasinnia",
    "gazonni-travi",
}

# Legacy slug-набори — лише для seed міграцій.
# Активна логіка: CatalogFilter.category_bindings у БД.

VOLUME_FILTER_ROOT_SLUGS = frozenset({
    "nasinnia",
    "dobriva-ta-stimuliatori-rostu",
    "zasobi-zakhistu-roslin",
    "grunti-ta-vse-dlia-posadki",
})
VOLUME_FILTER_EXTRA_SLUGS = frozenset({
    "vagove-nasinnia",
})


def category_allows_catalog_filter(category, catalog_filter):
    """Чи показувати фільтр для категорії (найближче налаштування в ланцюгу)."""
    bindings = {
        b.category_id: b.is_enabled
        for b in catalog_filter.category_bindings.all()
    }
    # Якщо привʼязок немає взагалі — показувати скрізь (у т.ч. корінь каталогу)
    if not bindings:
        return True

    if category is None:
        return any(bindings.values())

    # Від листа до кореня — перше явне налаштування перемагає
    for node in reversed(category.breadcrumb_chain()):
        if node.pk in bindings:
            return bindings[node.pk]
    return False


def category_allows_volume_filter(category):
    """Сумісність зі старим API."""
    from .filter_models import CatalogFilter

    cf = CatalogFilter.objects.filter(slug="volume", is_active=True).first()
    if not cf:
        return False
    return category_allows_catalog_filter(category, cf)


# Підпис на картці та сторінці товару: лише обʼєм / вага / кількість шт.
WEIGHT_PACK_SLUGS = frozenset({"vagove-nasinnia"})
PIECES_PACK_ROOT_SLUGS = frozenset({
    "nasinnia",
    "posadkovii-material",
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
    "zakhist-vid-pobutovikh-shkidnikiv",
})
VOLUME_PACK_ROOT_SLUGS = frozenset({"grunti-ta-vse-dlia-posadki"})
MIXED_PACK_ROOT_SLUGS = frozenset({
    "dobriva-ta-stimuliatori-rostu",
    "zasobi-zakhistu-roslin",
})

_PACK_LABELS = {
    "volume": ("Обʼєм", "Объём"),
    "weight": ("Вага", "Вес"),
    "pieces": ("Кількість шт", "Количество шт"),
}
_PACK_OPTION_LABELS = {
    "volume": ("100 мл", "500 мл", "1 л"),
    "weight": ("10 г", "50 г", "100 г"),
    "pieces": ("5 шт", "10 шт", "20 шт"),
}
_SIZE_LABELS = frozenset({"S", "M", "L", "s", "m", "l"})
_SIZE_INDEX = {"S": 0, "M": 1, "L": 2}

_WEIGHT_UNIT_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:кг|г)(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
_VOLUME_UNIT_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:мл|л)(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
_PIECE_UNIT_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*шт(?![а-яіїєґa-z])",
    re.IGNORECASE,
)


def category_slug_chain(category):
    """Від кореня до поточної категорії (працює і з historical-моделлю)."""
    chain = []
    node = category
    guard = 0
    while node is not None and guard < 8:
        chain.append(getattr(node, "slug", "") or "")
        node = getattr(node, "parent", None)
        guard += 1
    chain.reverse()
    return chain


def pack_unit_kind(pack_volume):
    """Обʼєм / вага / штуки за одиницею виміру."""
    text = pack_volume or ""
    if _WEIGHT_UNIT_RE.search(text):
        return "weight"
    if _VOLUME_UNIT_RE.search(text):
        return "volume"
    if _PIECE_UNIT_RE.search(text):
        return "pieces"
    return None


def pack_measure_kind(category, pack_volume):
    """Який підпис показувати: обʼєм, вага або кількість штук.

    Ґрунти — завжди обʼєм. Вагове насіння — вага.
    Решта насіння та посадковий матеріал — кількість штук.
    Добрива і засоби захисту: сухі (г/кг) — вага, рідкі — обʼєм.
    """
    unit_kind = pack_unit_kind(pack_volume)
    if category is None:
        return unit_kind or "pieces"

    slugs = category_slug_chain(category)
    if any(slug in WEIGHT_PACK_SLUGS for slug in slugs):
        return "weight"

    root = slugs[0] if slugs else ""
    if root in PIECES_PACK_ROOT_SLUGS:
        return "pieces"
    if root in VOLUME_PACK_ROOT_SLUGS:
        return "volume"
    if root in MIXED_PACK_ROOT_SLUGS:
        if unit_kind == "weight":
            return "weight"
        if unit_kind == "pieces":
            return "pieces"
        return "volume"
    return unit_kind or "pieces"


def pack_option_labels(kind):
    return list(_PACK_OPTION_LABELS.get(kind or "pieces", _PACK_OPTION_LABELS["pieces"]))


def pack_measure_label(category, pack_volume):
    """Підпис біля варіантів: Обʼєм / Вага / Кількість шт."""
    from apps.core.i18n_utils import is_ru

    labels = _PACK_LABELS.get(pack_measure_kind(category, pack_volume), _PACK_LABELS["pieces"])
    uk, ru = labels
    if is_ru():
        return ru
    return uk


def rewrite_size_variant_labels(product):
    """Замінює демо-кнопки S/M/L на обʼєм, вагу або кількість шт."""
    variants = list(product.variants.order_by("order", "id"))
    if not variants:
        return False
    if not all((getattr(item, "label", "") or "").strip() in _SIZE_LABELS for item in variants):
        return False
    labels = pack_option_labels(pack_measure_kind(product.category, product.pack_volume))
    for variant in variants:
        idx = _SIZE_INDEX.get((variant.label or "").strip().upper(), 0)
        variant.label = labels[min(idx, len(labels) - 1)]
        variant.save(update_fields=["label"])
    if not (product.pack_volume or "").strip():
        product.pack_volume = labels[0]
        product.save(update_fields=["pack_volume"])
    cache = getattr(product, "_prefetched_objects_cache", None)
    if cache:
        cache.pop("variants", None)
    return True
