"""Підказки для адмінки — коротко і зрозуміло (без техжаргону)."""

from __future__ import annotations

# Підказки на рівні всієї секції CMS (шапка редактора)
SECTION_HINTS: dict[tuple[str, str], str] = {
    ("home", "hero"): (
        "Банер на головній: фото, заголовок, короткий підпис і кнопки. "
        "Порожнє фото — лишиться стандартне."
    ),
    ("home", "trust"): (
        "Смужка довіри під банером. Тут лише увімкнення секції; "
        "тексти пунктів — у розділі «Контент → Переваги»."
    ),
    ("home", "categories"): (
        "Блок «Категорії» на головній. "
        "Картинки плиток і пунктів меню змінюйте в «Меню → 1 рівень категорій»."
    ),
    ("home", "hits"): (
        "Секція «Хіти». Які товари показувати — позначкою «Хіт» у картці товару."
    ),
    ("home", "news"): (
        "Секція «Новинки». Товари — позначкою «Новинка» у картці товару."
    ),
    ("home", "story"): (
        "Три історії на головній: фото, заголовок і короткий текст кожної картки."
    ),
    ("home", "benefits"): (
        "Блок переваг. Увімкнення тут; тексти карток — у «Контент → Переваги»."
    ),
    ("home", "sale"): (
        "Блок акцій на головній. Товари — позначкою «Акція» у картці товару."
    ),
    ("home", "reviews"): (
        "Відгуки на головній. Самі відгуки — у «Контент → Відгуки»."
    ),
    ("site", "header"): (
        "Шапка сайту: рядок-анонс угорі та підписи пунктів меню."
    ),
    ("site", "footer"): (
        "Підвал: заголовки колонок, короткий заклик і фото фону для підписки на email. "
        "Порожнє фото — стандартне."
    ),
    ("site", "lead_modal"): (
        "Спливаюче вікно заявки («Купити в 1 клік» тощо): заголовок, підказки полів і фото знизу. "
        "Порожнє фото — стандартне (соняшники)."
    ),
    ("site", "fab"): (
        "Кругла кнопка звʼязку в кутку екрана."
    ),
    ("site", "cart_drawer"): (
        "Бічна панель кошика: підписи кнопок і текст, коли кошик порожній."
    ),
    ("about", "intro"): (
        "Вступ на сторінці «Про нас»: заголовок і основний текст."
    ),
    ("about", "shelves"): (
        "Список на поличках: заголовок і пункти окремо. Порожній пункт на сайті не покажеться."
    ),
    ("about", "timeline"): (
        "Хронологія: рік, назва етапу, короткий текст і фото."
    ),
    ("about", "philosophy"): (
        "Блок філософії бренду: заголовок і кілька абзаців тексту."
    ),
    ("about", "why"): (
        "«Чому ми»: короткі заголовки пунктів і пояснення до них."
    ),
    ("about", "produce"): (
        "Заклик унизу сторінки «Про нас»: заголовок, кнопка і фото фону."
    ),
    ("delivery", "page"): (
        "Сторінка доставки і оплати: заголовки блоків і тексти з поясненнями."
    ),
    ("certificates", "page"): (
        "Сторінка сертифікатів: заголовок і короткий вступ. "
        "Самі файли — у «Контент → Сертифікати»."
    ),
    ("contacts", "page"): (
        "Контакти. Чотири крамниці: назва, адреса, за потреби телефон і графік. "
        "Соцмережі беруться з налаштувань сайту."
    ),
    ("offer", "page"): (
        "Публічна оферта — повний юридичний текст сторінки."
    ),
    ("privacy", "page"): (
        "Політика конфіденційності — повний текст сторінки."
    ),
    ("error", "page404"): (
        "Сторінка «не знайдено»: заголовок, короткий текст і кнопка."
    ),
    ("catalog", "page"): (
        "Тексти сторінки каталогу: заголовок і повідомлення, коли товарів немає."
    ),
    ("catalog", "filters"): (
        "Підписи груп фільтрів у каталозі."
    ),
    ("search", "page"): (
        "Пошук: підказка в полі і текст, коли нічого не знайдено."
    ),
    ("cart", "page"): (
        "Сторінка кошика: заголовки й підписи кнопок."
    ),
    ("checkout", "page"): (
        "Оформлення замовлення: підписи полів і кнопок."
    ),
    ("thankyou", "page"): (
        "Сторінка після замовлення: заголовок і короткий текст подяки."
    ),
    ("wishlist", "page"): (
        "Обране: заголовок і текст, коли список порожній."
    ),
    ("product", "page"): (
        "Картка товару: підписи статусу наявності, кнопок купівлі, сердечка і бейджів."
    ),
}

# Підказки для полів за типом ключа
TEXT_HINTS = {
    "title": "Короткий заголовок — щоб зручно читався на телефоні.",
    "lead": "Одне-два короткі речення.",
    "body": "Кілька абзаців звичайним текстом. Enter — новий абзац.",
    "long": "Повний текст сторінки. Пишіть як звичайно; абзаци зʼявляться самі.",
    "cta": "Текст кнопки — кілька слів.",
    "label": "Короткий підпис.",
    "announce": "Рядок у верхній смузі сайту. Суму безкоштовної доставки можна вписати в текст, наприклад «від 1500 ₴».",
    "placeholder": "Підказка всередині порожнього поля.",
    "visible": "Увімкніть, щоб цей блок показувався на сайті.",
}

IMAGE_HINTS = {
    "hero": "Фото для банера, краще ширше за висоту. Якщо не завантажити — лишиться стандартне.",
    "story": "Фото до картки історії. Якщо не завантажити — лишиться стандартне.",
    "timeline": "Фото до етапу історії. Якщо порожньо — покажеться стандартне.",
    "produce": "Фото фону для блоку-заклику. Якщо порожньо — стандартне.",
    "footer": "Фото фону для підписки на email. Якщо порожньо — стандартне.",
    "modal": "Фото внизу спливаючого вікна. Якщо порожньо — стандартне (соняшники).",
    "banner": "Фото банера, краще горизонтальне.",
    "block": "Завантажте своє фото або залиште порожнім — тоді буде стандартне з сайту.",
}

# Меню категорій (1 / 2 / 3 рівень)
CATEGORY_LEVEL_HINTS = {
    1: (
        "Головні розділи меню й плитки на головній. "
        "Коротка назва. Іконку можна завантажити або лишити порожньою — візьметься стандартна."
    ),
    2: (
        "Підрозділ усередині головної категорії. "
        "Коротка назва. Іконка не обовʼязкова."
    ),
    3: (
        "Уточнення всередині підкатегорії. "
        "Коротка назва. Іконка не обовʼязкова."
    ),
}

CATEGORY_FIELD_HINTS = {
    "name": "Назва, яку бачать покупці.",
    "erp_name": "Лише якщо в касі назва інша. Інакше залиште порожнім.",
    "slug": "Краще не змінювати — заповниться само з назви.",
    "description": "Короткий опис категорії (необовʼязково).",
    "order": "Менше число — вище в списку.",
    "image_level_1": "Іконка для меню. Якщо порожньо — стандартна з сайту.",
    "image_level_2": "Необовʼязково. Якщо порожньо — покажеться соняшник.",
    "image_level_3": "Необовʼязково. Якщо порожньо — покажеться соняшник.",
}


def help_for_section(page_slug: str, section_slug: str) -> str:
    return SECTION_HINTS.get((page_slug, section_slug), "")


def help_for_image(profile: str = "block") -> str:
    return IMAGE_HINTS.get(profile, IMAGE_HINTS["block"])


def help_for_key(key: str, page: str = "") -> str:
    if is_visibility_like(key):
        return TEXT_HINTS["visible"]

    if key.endswith("_image") or key == "image":
        if "story" in key:
            return help_for_image("story")
        if "timeline" in key:
            return help_for_image("timeline")
        if "produce" in key:
            return help_for_image("produce")
        if "footer_cta" in key or (key.startswith("footer_") and key.endswith("_image")):
            return help_for_image("footer")
        if "lead_modal" in key or "modal" in key:
            return help_for_image("modal")
        if "hero" in key or "banner" in key:
            return help_for_image("hero" if "hero" in key else "banner")
        return help_for_image("block")

    if key.startswith("shelves_item_"):
        return "Один пункт списку. Порожнє поле на сайті не покажеться."
    if key == "free_note":
        return "Суму безкоштовної доставки пишіть прямо в тексті, наприклад «від 1500 ₴»."
    if "announce" in key:
        return TEXT_HINTS["announce"]
    if key.endswith("_placeholder") or key.endswith("_ph"):
        return TEXT_HINTS["placeholder"]
    if key.endswith("_label"):
        return TEXT_HINTS["label"]
    if key.endswith("_btn") or "cta" in key:
        return TEXT_HINTS["cta"]
    if key.endswith("_title") or key.endswith("_name") or key.endswith("_crumb"):
        return TEXT_HINTS["title"]
    if "lead" in key:
        return TEXT_HINTS["lead"]
    if page in {"offer", "privacy"} and (
        key.endswith("_body") or key.endswith("_html") or key.endswith("_text")
    ):
        return TEXT_HINTS["long"]
    if key.endswith("_body") or key in {"philosophy_text", "intro_body"}:
        return (
            "Основний текст блоку. Пишіть звичайними реченнями — "
            "абзаци можна робити клавішею Enter. Жирний, списки й посилання — кнопками зверху."
        )
    if key.endswith("_html"):
        return (
            "Текст блоку. Enter — новий абзац. "
            "Жирний, списки й посилання — кнопками зверху."
        )
    if key.endswith("_text") or key.endswith("_empty") or "empty_" in key:
        return TEXT_HINTS["lead"]
    return ""


def is_visibility_like(key: str) -> bool:
    return key.endswith("_visible") or key == "section_visible"


def help_for_category_level(level: int) -> str:
    return CATEGORY_LEVEL_HINTS.get(level, "")


def help_for_category_field(field: str, level: int) -> str:
    if field == "image":
        return CATEGORY_FIELD_HINTS.get(f"image_level_{level}", CATEGORY_FIELD_HINTS["image_level_1"])
    return CATEGORY_FIELD_HINTS.get(field, "")
