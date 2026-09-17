"""Дефолти SiteBlock: (page, key) → значення, labels, типи."""

from __future__ import annotations

BLOCK_CONTENT_TYPES: dict[tuple[str, str], str] = {}
BLOCK_LABELS: dict[tuple[str, str], str] = {}
BLOCK_DEFAULTS: dict[tuple[str, str], str] = {}
STATIC_FALLBACKS: dict[tuple[str, str], str] = {}
INLINE_KEYS: set[tuple[str, str]] = set()
MULTILINE_KEYS: set[tuple[str, str]] = set()
URL_KEYS: set[tuple[str, str]] = set()
IMAGE_KEYS: set[tuple[str, str]] = set()


def _reg(
    page: str,
    key: str,
    default: str = "",
    *,
    label: str = "",
    content_type: str = "text",
    inline: bool = False,
    multiline: bool = False,
) -> None:
    pair = (page, key)
    BLOCK_DEFAULTS[pair] = default
    BLOCK_LABELS[pair] = label or key
    BLOCK_CONTENT_TYPES[pair] = content_type
    if content_type == "url":
        URL_KEYS.add(pair)
    elif content_type == "image":
        IMAGE_KEYS.add(pair)
    if inline:
        INLINE_KEYS.add(pair)
    if multiline:
        MULTILINE_KEYS.add(pair)


def is_visibility_key(key: str) -> bool:
    return key.endswith("_visible")


def visibility_default(key: str) -> str:
    return "1" if is_visibility_key(key) else ""


# --- Home: hero (фото в HeroSlide) ---
_reg("home", "hero_section_visible", "1", label="Показувати Hero")

# --- Home: trust ---
_reg("home", "trust_section_visible", "1", label="Показувати смугу довіри")

# --- Home: categories ---
_reg("home", "categories_section_visible", "1", label="Показувати категорії")
_reg("home", "categories_title", "Категорії каталогу", label="Заголовок", inline=True)
_reg("home", "categories_link_label", "Усі категорії", label="Текст посилання", inline=True)
_reg("home", "categories_link", "/katalog/", label="Посилання", content_type="url")

# --- Home: hits ---
_reg("home", "hits_section_visible", "1", label="Показувати хіти")
_reg("home", "hits_title", "Хіти продажу", label="Заголовок", inline=True)
_reg("home", "hits_link_label", "У каталог", label="Текст посилання", inline=True)
_reg("home", "hits_link", "/katalog/aktsiyi/", label="Посилання", content_type="url")

# --- Home: news ---
_reg("home", "news_section_visible", "1", label="Показувати новинки")
_reg("home", "news_title", "Новинки сезону", label="Заголовок", inline=True)

# --- Home: story (3 картки) ---
_reg("home", "story_section_visible", "1", label="Показувати історії")
_reg(
    "home",
    "story_title",
    "Вирощуємо довіру разом із вашим урожаєм",
    label="Заголовок секції",
    inline=True,
)
for i, (title, text, cta, url, img) in enumerate(
    [
        (
            "Власне виробництво",
            "Частину асортименту виробляємо самостійно. Відбираємо партії, перевіряємо схожість і пакуємо так, щоб насіння доїхало до вас у відмінному стані.",
            "Про нас",
            "/pro-nas/",
            "img/home/story-grow.webp",
        ),
        (
            "Про нас",
            "Ваш успіх у городі — наш головний орієнтир. Ділимося досвідом, допомагаємо з вибором і супроводжуємо від посіву до врожаю.",
            "Про компанію",
            "/pro-nas/",
            "img/home/story-sustain.webp",
        ),
        (
            "Оригінальна продукція",
            "Засоби захисту рослин, насіння та добрива від найкращих світових та українських виробників. Ви можете бути впевнені в якості та безпечності кожного товару.",
            "До каталогу",
            "/katalog/aktsiyi/",
            "img/home/story-harvest.webp",
        ),
    ],
    start=1,
):
    _reg("home", f"story_{i}_title", title, label=f"Картка {i}: заголовок", inline=True)
    _reg("home", f"story_{i}_text", text, label=f"Картка {i}: текст", multiline=True)
    _reg("home", f"story_{i}_cta_label", cta, label=f"Картка {i}: кнопка", inline=True)
    _reg("home", f"story_{i}_cta", url, label=f"Картка {i}: посилання", content_type="url")
    _reg("home", f"story_{i}_image", "", label=f"Картка {i}: фото", content_type="image")
    STATIC_FALLBACKS[("home", f"story_{i}_image")] = img

# --- Home: benefits ---
_reg("home", "benefits_section_visible", "1", label="Показувати переваги")

# --- Home: sale ---
_reg("home", "sale_section_visible", "1", label="Показувати акції")
_reg("home", "sale_title", "Акції та знижки", label="Заголовок", inline=True)
_reg("home", "sale_link_label", "Усі акції", label="Текст посилання", inline=True)
_reg("home", "sale_link", "/katalog/aktsiyi/", label="Посилання", content_type="url")

# --- Home: reviews ---
_reg("home", "reviews_section_visible", "1", label="Показувати відгуки")
_reg("home", "reviews_title", "Відгуки покупців", label="Заголовок", inline=True)

# --- Site: header (item-level visibility) ---
_reg("site", "header_announce_text", "Безкоштовна доставка від {threshold} ₴ · Відправка наступного дня", label="Текст анонсу", inline=True)
_reg("site", "header_announce_visible", "1", label="Показувати анонс")
_reg("site", "header_nav_home_visible", "1", label="Пункт «Головна»")
_reg("site", "header_nav_catalog_visible", "1", label="Пункт «Каталог»")
_reg("site", "header_nav_about_visible", "1", label="Пункт «Про нас»")
_reg("site", "header_nav_contacts_visible", "1", label="Пункт «Контакти»")
_reg("site", "header_search_visible", "1", label="Пошук")
_reg("site", "header_lang_visible", "1", label="Перемикач мови")
_reg("site", "header_wishlist_visible", "1", label="Обране")
_reg("site", "header_cart_visible", "1", label="Кошик")
_reg("site", "header_nav_home_label", "Головна", label="Текст «Головна»", inline=True)
_reg("site", "header_nav_catalog_label", "Каталог", label="Текст «Каталог»", inline=True)
_reg("site", "header_nav_about_label", "Про нас", label="Текст «Про нас»", inline=True)
_reg("site", "header_nav_contacts_label", "Контакти", label="Текст «Контакти»", inline=True)
_reg("site", "header_search_placeholder", "Пошук", label="Placeholder пошуку", inline=True)

# --- Site: footer ---
_reg("site", "footer_cta_visible", "1", label="Показувати newsletter")
_reg("site", "footer_cta_title", "Новини саду на email", label="Заголовок newsletter", inline=True)
_reg(
    "site",
    "footer_cta_text",
    "Поради з вирощування, сезонні акції та новинки асортименту — без зайвого шуму.",
    label="Текст newsletter",
    multiline=True,
)
_reg("site", "footer_cta_btn", "Підписатись", label="Кнопка newsletter", inline=True)
_reg("site", "footer_col_cats_title", "Категорії", label="Колонка категорій", inline=True)
_reg("site", "footer_col_info_title", "Інформація", label="Колонка інформації", inline=True)
_reg("site", "footer_col_contacts_title", "Контакти", label="Колонка контактів", inline=True)
_reg("site", "footer_link_about_visible", "1", label="Посилання «Про нас»")
_reg("site", "footer_link_delivery_visible", "1", label="Посилання «Доставка»")
_reg("site", "footer_link_offer_visible", "1", label="Посилання «Оферта»")
_reg("site", "footer_copyright", "© {year} {site_name}. Усі права захищено.", label="Copyright", inline=True)

# --- Site: lead modal ---
_reg("site", "lead_modal_visible", "1", label="Показувати модалку")
_reg("site", "lead_modal_title", "Не йдіть без подарунка!", label="Заголовок", inline=True)
_reg(
    "site",
    "lead_modal_lead",
    "Залиште номер телефону — передзвонимо і підкажемо знижку та найкращі товари під ваш запит.",
    label="Підзаголовок",
    multiline=True,
)
_reg("site", "lead_modal_cta", "Отримати знижку", label="Кнопка", inline=True)
_reg("site", "lead_modal_success_title", "Дякуємо!", label="Успіх: заголовок", inline=True)
_reg(
    "site",
    "lead_modal_success_text",
    "Ми зв'яжемось з вами найближчим часом.",
    label="Успіх: текст",
    multiline=True,
)
_reg("site", "lead_modal_agree", "Погоджуюсь на обробку персональних даних", label="Чекбокс згоди", inline=True)

# --- Site: fab ---
_reg("site", "fab_visible", "1", label="Показувати кнопку швидкого звʼязку")

# --- About ---
_reg("about", "intro_section_visible", "1", label="Показувати інтро")
_reg("about", "intro_title", "Торговельна марка «Соняшник»", label="Заголовок", inline=True)
_reg("about", "intro_lead", "Має більше 20 років досвіду з вирощування рослин та їх захисту.", label="Лід", multiline=True)
_reg(
    "about",
    "intro_body",
    "Ми впевнені: найякісніші продукти — вирощені на власній землі, а найщасливіші люди — ті, що мають можливість до землі доторкнутись.\n\n"
    "ТМ «Соняшник» є офіційним представником найкращих аграрних брендів України та світу.\n\n"
    "Продукція представлена у крамницях мережі «Соняшник» завжди якісна та сертифікована. Ми працюємо з найкращими виробниками, завжди маємо свіжу продукцію, що зберігається із дотриманням усіх необхідних умов.\n\n"
    "Ми щиро віримо у світле аграрне майбутнє нашої країни, обожнюємо нашу справу та віддано допомагаємо клієнтам отримати найкращі врожаї, найквітучіші сади та затишні зелені куточки — де б ви не знаходились.",
    label="Текст",
    multiline=True,
)

_reg("about", "shelves_section_visible", "1", label="Показувати полички")
_reg("about", "shelves_title", "На поличках наших крамниць завжди є", label="Заголовок", inline=True)
_reg(
    "about",
    "shelves_list",
    "Найкраще пакетоване та вагове насіння з усього світу (Україна, Голландія, Данія, Японія, Польща, Молдова, Франція та інші)\n"
    "Добрива та стимулятори росту\n"
    "Найдієвіші засоби захисту рослин від хвороб та шкідників\n"
    "БІО-захист рослин\n"
    "Добрива для всіх видів садових та кімнатних рослин\n"
    "Садовий інструмент\n"
    "Системи крапельного зрошування та поливу\n"
    "Все для кімнатних рослин\n"
    "Усі супутні товари, що можуть вам знадобитись",
    label="Список (по рядку)",
    multiline=True,
)

_reg("about", "timeline_section_visible", "1", label="Показувати хронологію")
_TIMELINE = [
    ("2003", "Перші кроки з землею", "Починаємо шлях у вирощуванні рослин та їх захисті — основа досвіду ТМ «Соняшник».", "img/about/apples.webp"),
    ("2012", "Мережа крамниць", "Розвиваємо мережу «Соняшник»: свіжа продукція від перевірених виробників із дотриманням умов зберігання.", "img/about/harvest-bag.webp"),
    ("2018", "Бренди світу й України", "Стаємо офіційним представником провідних аграрних брендів. Асортимент — насіння, захист, добрива, інструмент і полив.", "img/about/field-hands.webp"),
    ("2026", "Вирощуй не шкодячи", "Консультації, схеми захисту на сезон, сертифікована продукція та підтримка в соцмережах — для саду, городу й кімнатних рослин.", ""),
]
for i, (year, name, text, img) in enumerate(_TIMELINE, start=1):
    _reg("about", f"timeline_{i}_year", year, label=f"Етап {i}: рік", inline=True)
    _reg("about", f"timeline_{i}_name", name, label=f"Етап {i}: назва", inline=True)
    _reg("about", f"timeline_{i}_text", text, label=f"Етап {i}: текст", multiline=True)
    if img:
        _reg("about", f"timeline_{i}_image", "", label=f"Етап {i}: фото", content_type="image")
        STATIC_FALLBACKS[("about", f"timeline_{i}_image")] = img

_reg("about", "philosophy_section_visible", "1", label="Показувати філософію")
_reg("about", "philosophy_title", "Наша філософія", label="Заголовок", inline=True)
_reg("about", "philosophy_motto", "Вирощуй не шкодячи.", label="Девіз", inline=True)
_reg(
    "about",
    "philosophy_text",
    "Ми пропонуємо раціональне використання добрив та засобів захисту рослин з максимальною користю для вас і мінімальною шкодою для навколишнього середовища. Ви завжди можете отримати ефективну консультацію з допомогою по догляду та використанню засобів, системою захисту рослини на сезон та схемами лікування для вашого саду або кімнатних зелених друзів.\n\n"
    "А наші соцмережі допоможуть вам розібратися з особливостями застосування препаратів на різних культурах та полегшать ведення рослинного господарства.",
    label="Текст",
    multiline=True,
)

_reg("about", "why_section_visible", "1", label="Показувати «Чому нас обирають»")
_reg("about", "why_title", "Чому нас обирають", label="Заголовок", inline=True)
_WHY = [
    ("100%", "оригінальної продукції від кращих світових та українських виробників. Засоби захисту рослин, насіння та добрива — ви можете бути впевнені в якості та безпечності кожного товару"),
    ("23", "роки досвіду вирощування рослин у саду, на городі та на підвіконні"),
    ("12", "місяців щороку тестуємо найкращі новинки на власній ділянці та рослинах"),
    ("1000 +", "товарів для саду й дому в каталозі"),
]
for i, (val, label) in enumerate(_WHY, start=1):
    _reg("about", f"why_{i}_value", val, label=f"Стат {i}: значення", inline=True)
    _reg("about", f"why_{i}_label", label, label=f"Стат {i}: підпис", multiline=True)

_reg("about", "produce_section_visible", "1", label="Показувати CTA")
_reg(
    "about",
    "produce_title",
    "Потрібно багато товару? Зателефонуйте нам — і ми запропонуємо індивідуальну вартість.",
    label="Заголовок CTA",
    multiline=True,
)
_reg("about", "produce_image", "", label="Фон CTA", content_type="image")
STATIC_FALLBACKS[("about", "produce_image")] = "img/about/produce-cta.webp"
_reg("about", "produce_btn_catalog", "До каталогу", label="Кнопка каталогу", inline=True)
_reg("about", "produce_btn_call", "Зателефонувати", label="Кнопка дзвінка", inline=True)

# --- Delivery ---
_reg("delivery", "page_section_visible", "1", label="Показувати сторінку")
_reg("delivery", "page_title", "Доставка і оплата", label="Заголовок", inline=True)
_reg("delivery", "methods_title", "Способи доставки", label="Заголовок доставки", inline=True)
_reg(
    "delivery",
    "methods_html",
    "<table class=\"delivery-table\"><tr><th>Спосіб</th><th>Сервіс</th><th>Термін</th></tr>"
    "<tr><td>Відділення</td><td>Нова Пошта</td><td>1–3 дні</td></tr>"
    "<tr><td>Поштомат</td><td>Нова Пошта</td><td>1–3 дні</td></tr>"
    "<tr><td>Кур'єр</td><td>Нова Пошта</td><td>1–3 дні</td></tr>"
    "<tr><td>Відділення / адреса</td><td>Укрпошта</td><td>2–5 днів</td></tr>"
    "<tr><td>Самовивіз</td><td>Власна точка</td><td>у день замовлення</td></tr></table>",
    label="Таблиця доставки (HTML)",
    multiline=True,
)
_reg(
    "delivery",
    "free_note",
    "Безкоштовна доставка при замовленні від {threshold} ₴.",
    label="Примітка про безкоштовну доставку",
    inline=True,
)
_reg("delivery", "payment_title", "Способи оплати", label="Заголовок оплати", inline=True)
_reg(
    "delivery",
    "payment_html",
    "<ul><li><strong>LiqPay</strong> — оплата карткою онлайн (у т.ч. Apple Pay / Google Pay).</li>"
    "<li><strong>Післяплата</strong> — оплата під час отримання на пошті.</li>"
    "<li><strong>При самовивозі</strong> — готівкою або терміналом у точці видачі.</li></ul>",
    label="Оплата (HTML)",
    multiline=True,
)
_reg("delivery", "faq_title", "Часті запитання", label="Заголовок FAQ", inline=True)
for i, (q, a) in enumerate(
    [
        ("Скільки коштує доставка?", "Вартість розраховується перевізником залежно від ваги та міста. При замовленні від {threshold} ₴ доставка безкоштовна."),
        ("Як швидко відправляють замовлення?", "Замовлення, оформлені до 15:00, відправляємо того ж дня, інші — наступного робочого дня."),
        ("Чи можна оплатити при отриманні?", "Так, доступна оплата післяплатою під час отримання посилки на пошті."),
    ],
    start=1,
):
    _reg("delivery", f"faq_{i}_q", q, label=f"FAQ {i}: питання", inline=True)
    _reg("delivery", f"faq_{i}_a", a, label=f"FAQ {i}: відповідь", multiline=True)

# --- Certificates / Contacts / Offer / Privacy ---
_reg("certificates", "page_section_visible", "1", label="Показувати сторінку")
_reg("certificates", "page_title", "Сертифікати власного виробництва", label="Заголовок", inline=True)
_reg("certificates", "page_lead", "", label="Підзаголовок", multiline=True)
_reg("certificates", "empty_text", "Сертифікати зʼявляться незабаром.", label="Порожній стан", inline=True)

_reg("contacts", "page_section_visible", "1", label="Показувати сторінку")
_reg("contacts", "page_title", "Контакти", label="Заголовок", inline=True)
_reg("contacts", "label_phone", "Телефон", label="Підпис телефону", inline=True)
_reg("contacts", "label_hours", "Графік роботи", label="Підпис графіка", inline=True)
_reg("contacts", "label_address", "Точка видачі", label="Підпис адреси", inline=True)
_reg("contacts", "form_title", "Написати нам", label="Заголовок форми", inline=True)
_reg("contacts", "form_cta", "Надіслати", label="Кнопка форми", inline=True)
_reg("contacts", "map_embed", "https://maps.google.com/maps?q=%D0%9A%D0%B8%D1%97%D0%B2%2C+%D0%A5%D1%80%D0%B5%D1%89%D0%B0%D1%82%D0%B8%D0%BA+1&hl=uk&z=16&output=embed", label="URL карти (embed)", inline=True)

_reg("offer", "page_section_visible", "1", label="Показувати сторінку")
_reg("offer", "page_title", "Договір публічної оферти", label="Заголовок", inline=True)
_reg(
    "offer",
    "page_body",
    "<p>Цей документ є офіційною пропозицією (публічною офертою) інтернет-магазину укласти договір купівлі-продажу товарів дистанційним способом на умовах, викладених нижче.</p>"
    "<h2>1. Загальні положення</h2><p>Оформлення замовлення на сайті означає повну та беззаперечну згоду покупця з умовами цього договору.</p>"
    "<h2>2. Предмет договору</h2><p>Продавець зобов'язується передати у власність покупця товар, а покупець зобов'язується оплатити та отримати товар на умовах цього договору.</p>"
    "<h2>3. Оформлення замовлення</h2><p>Замовлення оформлюється через форму на сайті. Після оформлення покупець отримує підтвердження та номер замовлення.</p>"
    "<h2>4. Оплата та доставка</h2><p>Оплата здійснюється одним із способів, зазначених на сторінці «Доставка і оплата». Доставка виконується службами Нова Пошта / Укрпошта або самовивозом.</p>"
    "<h2>5. Повернення товару</h2><p>Повернення та обмін товару здійснюються згідно з чинним законодавством України про захист прав споживачів.</p>",
    label="Текст оферти (HTML)",
    multiline=True,
)

_reg("privacy", "page_section_visible", "1", label="Показувати сторінку")
_reg("privacy", "page_title", "Політика конфіденційності", label="Заголовок", inline=True)
_reg(
    "privacy",
    "page_body",
    "<p>Ця політика визначає порядок обробки персональних даних користувачів сайту.</p>"
    "<h2>1. Які дані ми збираємо</h2><ul>"
    "<li>Ім'я, номер телефону, email — при оформленні замовлення чи заявки.</li>"
    "<li>Адреса доставки — для передачі службам доставки.</li>"
    "<li>Технічні дані (cookies) — для коректної роботи сайту.</li></ul>"
    "<h2>2. Мета обробки даних</h2><p>Дані використовуються виключно для обробки замовлень, зв'язку з покупцем та покращення роботи сайту.</p>"
    "<h2>3. Захист даних</h2><p>Сайт не зберігає дані банківських карток. Оплата обробляється через захищений сервіс LiqPay.</p>"
    "<h2>4. Права користувача</h2><p>Користувач має право вимагати видалення чи уточнення своїх персональних даних, звернувшись через сторінку «Контакти».</p>",
    label="Текст політики (HTML)",
    multiline=True,
)

# --- Catalog / Search / Cart / Checkout / Thankyou / 404 ---
_reg("catalog", "page_section_visible", "1", label="Показувати контент")
_reg("catalog", "page_title", "Каталог", label="Заголовок каталогу", inline=True)
_reg("catalog", "empty_title", "Товарів не знайдено", label="Порожній: заголовок", inline=True)
_reg("catalog", "empty_text", "Спробуйте змінити фільтри або перегляньте інші категорії.", label="Порожній: текст", multiline=True)

_reg("search", "page_section_visible", "1", label="Показувати контент")
_reg("search", "page_title", "Результати пошуку", label="Заголовок", inline=True)
_reg("search", "hint_text", "Введіть назву товару або код у поле пошуку в шапці сайту.", label="Підказка без запиту", multiline=True)
_reg("search", "empty_title", "Нічого не знайдено", label="Порожній: заголовок", inline=True)
_reg("search", "empty_text", "Спробуйте інший запит або перегляньте каталог.", label="Порожній: текст", multiline=True)
_reg("search", "empty_cta", "До каталогу", label="Порожній: кнопка", inline=True)

_reg("cart", "page_section_visible", "1", label="Показувати контент")
_reg("cart", "page_title", "Ваш кошик", label="Заголовок", inline=True)
_reg("cart", "empty_title", "Кошик порожній", label="Порожній: заголовок", inline=True)
_reg("cart", "empty_text", "Додайте товари з каталогу, щоб оформити замовлення.", label="Порожній: текст", multiline=True)
_reg("cart", "empty_cta", "До каталогу", label="Порожній: кнопка", inline=True)

_reg("checkout", "page_section_visible", "1", label="Показувати контент")
_reg("checkout", "page_title", "Оформлення замовлення", label="Заголовок", inline=True)

_reg("thankyou", "page_section_visible", "1", label="Показувати контент")
_reg("thankyou", "page_title", "Дякуємо за замовлення!", label="Заголовок", inline=True)
_reg("thankyou", "page_lead", "Ми отримали ваше замовлення і звʼяжемось за потреби.", label="Підзаголовок", multiline=True)

_reg("error", "page_404_visible", "1", label="Показувати сторінку 404")
_reg("error", "page_404_title", "Сторінку не знайдено", label="Заголовок", inline=True)
_reg(
    "error",
    "page_404_text",
    "Можливо, вона переміщена або більше не існує. Скористайтесь пошуком або поверніться на головну.",
    label="Текст",
    multiline=True,
)
_reg("error", "page_404_cta_home", "На головну", label="Кнопка на головну", inline=True)
_reg("error", "page_404_cta_catalog", "До каталогу", label="Кнопка в каталог", inline=True)

# Фаза 2 — shop blocks (cart drawer, wishlist, filters, PDP, sale nav)
from apps.core import block_defaults_shop  # noqa: E402,F401


def get_block_default(page: str, key: str) -> str:
    if is_visibility_key(key):
        return BLOCK_DEFAULTS.get((page, key), "1")
    return BLOCK_DEFAULTS.get((page, key), "")


def get_block_label(page: str, key: str) -> str:
    return BLOCK_LABELS.get((page, key), key)


def get_block_content_type(page: str, key: str) -> str:
    return BLOCK_CONTENT_TYPES.get((page, key), "text")
