"""Фаза 2 CMS: cart_drawer, wishlist, catalog filters/listing, PDP, header sale."""

from apps.core.block_defaults import _reg

# --- Site: cart drawer ---
_reg("site", "cart_drawer_visible", "1", label="Показувати шторку кошика")
_reg("site", "cart_drawer_title", "Кошик", label="Заголовок", inline=True)
_reg("site", "cart_drawer_empty", "Кошик порожній", label="Порожній стан", inline=True)
_reg("site", "cart_drawer_remove", "Видалити", label="Кнопка видалення", inline=True)
_reg("site", "cart_drawer_total", "Разом", label="Підсумок", inline=True)
_reg("site", "cart_drawer_view", "Переглянути кошик", label="Кнопка «Переглянути»", inline=True)
_reg("site", "cart_drawer_checkout", "Оформити замовлення", label="Кнопка оформлення", inline=True)

# --- Site: header sale ---
_reg("site", "header_nav_sale_visible", "1", label="Пункт «Акції»")
_reg("site", "header_nav_sale_label", "Акції", label="Текст «Акції»", inline=True)

# --- Catalog listing extras ---
_reg("catalog", "sale_title", "Акції та знижки", label="Заголовок акцій", inline=True)
_reg("catalog", "sale_crumb", "Акції / знижки", label="Хлібна крихта акцій", inline=True)
_reg("catalog", "count_label", "Знайдено: {count} товар(ів)", label="Лічильник (використайте {count})", inline=True)
_reg("catalog", "filters_btn", "Фільтри", label="Кнопка фільтрів", inline=True)
_reg("catalog", "sort_popularity", "За популярністю", label="Сорт: популярність", inline=True)
_reg("catalog", "sort_price_asc", "Спочатку дешевші", label="Сорт: дешевші", inline=True)
_reg("catalog", "sort_price_desc", "Спочатку дорожчі", label="Сорт: дорожчі", inline=True)
_reg("catalog", "sort_new", "Новинки", label="Сорт: новинки", inline=True)
_reg("catalog", "empty_cta", "На головну", label="Порожній: кнопка", inline=True)

# --- Catalog filters ---
_reg("catalog", "filters_section_visible", "1", label="Показувати панель фільтрів")
_reg("catalog", "filters_title", "Фільтри", label="Заголовок панелі", inline=True)
_reg("catalog", "filters_price", "Ціна, ₴", label="Група ціни", inline=True)
_reg("catalog", "filters_price_min_ph", "від", label="Placeholder «від»", inline=True)
_reg("catalog", "filters_price_max_ph", "до", label="Placeholder «до»", inline=True)
_reg("catalog", "filters_in_stock", "Тільки в наявності", label="Чекбокс наявності", inline=True)
_reg("catalog", "filters_own", "Власне виробництво", label="Чекбокс власного", inline=True)
_reg("catalog", "filters_brand", "Бренд", label="Група бренду", inline=True)
_reg("catalog", "filters_country", "Країна виробник", label="Група країни", inline=True)
_reg("catalog", "filters_volume", "Обʼєм / фасування", label="Група обʼєму", inline=True)
_reg("catalog", "filters_reset", "Скинути", label="Кнопка скинути", inline=True)
_reg("catalog", "filters_apply", "Показати", label="Кнопка показати", inline=True)

# --- Wishlist ---
_reg("wishlist", "page_section_visible", "1", label="Показувати сторінку")
_reg("wishlist", "page_title", "Обране", label="Заголовок", inline=True)
_reg("wishlist", "loading", "Завантаження…", label="Текст завантаження", inline=True)
_reg("wishlist", "empty_title", "Поки порожньо", label="Порожній: заголовок", inline=True)
_reg(
    "wishlist",
    "empty_text",
    "Додавайте товари сердечком на картках або на сторінці товару.",
    label="Порожній: текст",
    multiline=True,
)
_reg("wishlist", "empty_cta", "До каталогу", label="Порожній: кнопка", inline=True)

# --- Product (PDP) ---
_reg("product", "page_section_visible", "1", label="Показувати контент PDP")
_reg("product", "badge_hit", "Хіт", label="Бейдж «Хіт»", inline=True)
_reg("product", "badge_new", "Новинка", label="Бейдж «Новинка»", inline=True)
_reg("product", "badge_sale", "Акція", label="Бейдж «Акція»", inline=True)
_reg("product", "badge_own", "Власне виробництво", label="Бейдж «Власне»", inline=True)
_reg("product", "sku_label", "Код:", label="Підпис коду", inline=True)
_reg("product", "volume_label", "Обʼєм:", label="Підпис обʼєму", inline=True)
_reg("product", "in_stock", "В наявності", label="В наявності", inline=True)
_reg("product", "out_of_stock", "Немає в наявності", label="Немає в наявності", inline=True)
_reg("product", "add_cart", "До кошика", label="Кнопка кошика", inline=True)
_reg("product", "one_click", "Купити в 1 клік", label="Кнопка 1 клік", inline=True)
_reg("product", "wish_off", "В обране", label="Обране: вимк", inline=True)
_reg("product", "wish_on", "В обраному", label="Обране: увімк", inline=True)
_reg("product", "desc_title", "Опис", label="Заголовок опису", inline=True)
_reg("product", "related_title", "Схожі товари", label="Схожі товари", inline=True)
