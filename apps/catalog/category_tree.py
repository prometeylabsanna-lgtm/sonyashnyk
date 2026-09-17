"""Повне дерево категорій каталогу (до 3 рівнів).

Акції/знижки — окремий маршрут /katalog/aktsiyi/, не категорія БД.
"""

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

POWER_FILTER_ROOT_SLUGS = frozenset({
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
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


def category_allows_power_filter(category):
    """Сумісність зі старим API."""
    from .filter_models import CatalogFilter

    cf = CatalogFilter.objects.filter(slug="power", is_active=True).first()
    if not cf:
        return False
    return category_allows_catalog_filter(category, cf)
