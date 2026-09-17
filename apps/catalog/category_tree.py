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

# Legacy slug-набори — використовуються лише для seed міграції / fallback.
# Активна логіка: CategoryFilterSetting у БД (адмінка «Фільтри»).

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


def _category_matches_slugs(category, root_slugs, extra_slugs=frozenset()):
    if category is None:
        return False
    for node in category.breadcrumb_chain():
        if node.slug in root_slugs or node.slug in extra_slugs:
            return True
    return False


def category_allows_filter(category, filter_type):
    """Чи показувати тип фільтра для категорії (найближче налаштування в ланцюгу)."""
    from .filter_models import CategoryFilterSetting

    if category is None:
        return CategoryFilterSetting.objects.filter(
            filter_type=filter_type,
            is_enabled=True,
        ).exists()

    chain_ids = [node.pk for node in category.breadcrumb_chain()]
    if not chain_ids:
        return False

    settings_map = {
        row.category_id: row.is_enabled
        for row in CategoryFilterSetting.objects.filter(
            category_id__in=chain_ids,
            filter_type=filter_type,
        )
    }
    # Від листа до кореня — перше явне налаштування перемагає
    for node in reversed(category.breadcrumb_chain()):
        if node.pk in settings_map:
            return settings_map[node.pk]
    return False


def category_allows_volume_filter(category):
    """Сумісність: делегує до CategoryFilterSetting."""
    from .filter_models import FilterType

    return category_allows_filter(category, FilterType.VOLUME)


def category_allows_power_filter(category):
    """Сумісність: делегує до CategoryFilterSetting."""
    from .filter_models import FilterType

    return category_allows_filter(category, FilterType.POWER)
