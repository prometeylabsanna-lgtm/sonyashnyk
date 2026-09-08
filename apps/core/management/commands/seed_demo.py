"""Наповнює БД тестовими (placeholder) даними для перевірки шаблонів.

Використання: python3 manage.py seed_demo
"""

from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductImage, ProductVariant
from apps.core.models import HeroSlide, HighlightPoint, Review

CATEGORY_TREE = [
    ("Насіння", ["Насіння овочів", "Насіння квітів", "Вагове насіння", "Газонні трави"]),
    ("Добрива та стимулятори росту", ["Добрива для газону", "Мінеральні добрива", "Органічні добрива"]),
    ("Засоби захисту рослин", ["Фунгіциди", "Інсектициди", "Гербіциди"]),
    ("Садовий інструмент", ["Секатори, ножі та ножиці", "Все для газону"]),
    ("Полив та оприскувачі", ["Оприскувачі", "Полив крапельний"]),
    ("Посадковий матеріал", ["Цибулини та бульби квітів", "Саджанці"]),
    ("Горщики", ["Пластикові горщики", "Керамічні горщики"]),
    ("Грунти та все для посадки", ["Субстрати", "Торфи"]),
]

BRANDS = ["АгроХім", "БіоСад", "Соняшник", "ЗеленСвіт"]
COUNTRIES = ["Україна", "Польща", "Нідерланди"]

# Назви без «товар N» — по 3 на підкатегорію
PRODUCT_NAMES = {
    "Насіння овочів": ["Томат «Де Барао»", "Огірок «Конкурент»", "Перець «Богатир»"],
    "Насіння квітів": ["Чорнобривці «Кармен»", "Петунія «Міраж»", "Цинія «Каліфорнія»"],
    "Вагове насіння": ["Газон ваговий «Спорт»", "Конюшина біла, 0.5 кг", "Люцерна посівна, 1 кг"],
    "Газонні трави": ["Газон «Універсал»", "Газон «Тіньовий»", "Газон «Спортивний»"],
    "Добрива для газону": ["Добриво для газону «Весна»", "Добриво для газону «Осінь»", "Газонне підживлення NPK"],
    "Мінеральні добрива": ["NPK 16-16-16", "Калійна селітра", "Суперфосфат подвійний"],
    "Органічні добрива": ["Біогумус «Соняшник»", "Компост-старт", "Кісткове борошно"],
    "Фунгіциди": ["Фунгіцид «Захист»", "Бордоська суміш", "Препарат від борошнистої роси"],
    "Інсектициди": ["Інсектицид «Актаро»", "Засіб від попелиці", "Біозахист від шкідників"],
    "Гербіциди": ["Гербіцид суцільної дії", "Засіб від бур'янів на газоні", "Селективний гербіцид"],
    "Секатори, ножі та ножиці": ["Секатор обвідний", "Садовий ніж", "Ножиці для живоплоту"],
    "Все для газону": ["Аератор ручний", "Граблі для газону", "Кромкоріз"],
    "Оприскувачі": ["Оприскувач 5 л", "Оприскувач 8 л", "Оприскувач акумуляторний"],
    "Полив крапельний": ["Набір крапельного поливу", "Крапельниця регульована", "Шланг поливний 20 м"],
    "Цибулини та бульби квітів": ["Тюльпан «Апелдорн»", "Нарцис «Ice Follies»", "Гладіолус суміш"],
    "Саджанці": ["Смородина чорна", "Аґрус «Інвікта»", "Малина «Полка»"],
    "Пластикові горщики": ["Горщик 1 л", "Горщик 3 л", "Горщик 5 л"],
    "Керамічні горщики": ["Кераміка Ø14 см", "Кераміка Ø18 см", "Кераміка Ø22 см"],
    "Субстрати": ["Субстрат універсальний", "Субстрат для розсади", "Субстрат для орхідей"],
    "Торфи": ["Торф верховий", "Торф низинний", "Торфосуміш посівна"],
}

SHORT_DESCS = {
    "Насіння овочів": ["Висока схожість, для відкритого ґрунту", "Ранній сорт для салатів і консервації", "Солодкий, товстостінний, урожайний"],
    "Насіння квітів": ["Яскраве цвітіння все літо", "Компактні кущі для клумб і кашпо", "Стійкі до спеки, довго цвітуть"],
    "Вагове насіння": ["Щільний покрив, зносостійкий", "Покращує ґрунт і фіксує азот", "Кормова й сидеральна культура"],
    "Газонні трави": ["Щільний зелений килим для ділянки", "Добре росте в затінку", "Витримує інтенсивне витоптування"],
    "Добрива для газону": ["Старт сезону, насичений колір", "Підготовка до зими", "Збалансоване живлення NPK"],
    "Мінеральні добрива": ["Універсальне мінеральне живлення", "Для плодоношення й стійкості", "Стимулює розвиток коренів"],
    "Органічні добрива": ["Натуральне живлення без хімії", "Прискорює дозрівання компосту", "Багате на фосфор і кальцій"],
    "Фунгіциди": ["Захист від грибкових хвороб", "Класичний профілактичний засіб", "Лікування борошнистої роси"],
    "Інсектициди": ["Швидка дія проти шкідників", "Безпечний для квітів і овочів", "Біологічний контроль шкідників"],
    "Гербіциди": ["Контроль бур'янів на ділянці", "Обережно для газонного покриву", "Цільова дія без шкоди культурі"],
    "Секатори, ножі та ножиці": ["Чистий зріз гілок до 20 мм", "Для щеплення та обрізки", "Рівний зріз живоплоту"],
    "Все для газону": ["Покращує дихання коренів", "Збирання сухої трави", "Охайний край газону"],
    "Оприскувачі": ["Зручний об'єм для городу", "Для кущів і плодових дерев", "Без постійного підкачування"],
    "Полив крапельний": ["Економія води, рівномірний полив", "Точкове зволоження рослин", "Міцний, гнучкий, UV-стійкий"],
    "Цибулини та бульби квітів": ["Класичний червоний тюльпан", "Раннє весняне цвітіння", "Яскрава суміш для клумби"],
    "Саджанці": ["Урожайна, зимостійка", "Крупноплідний, малошипний", "Ремонтантний сорт"],
    "Пластикові горщики": ["Для розсади та кімнатних", "Універсальний об'єм", "Для кущів і великих рослин"],
    "Керамічні горщики": ["Дихний матеріал, стильний вигляд", "Середній розмір для квітів", "Для великих кімнатних рослин"],
    "Субстрати": ["Готова суміш для більшості культур", "Легкий, для дружних сходів", "Повітропроникний, з корою"],
    "Торфи": ["Кислий, для підкислення ґрунту", "Поживний для грядок", "Ідеальний старт для насіння"],
}


class Command(BaseCommand):
    help = "Наповнює БД демо-даними (категорії, товари, банери) для перевірки верстки."

    def handle(self, *args, **options):
        self.seed_categories()
        self.seed_products()
        self.seed_product_images()
        self.seed_home_content()
        self.stdout.write(self.style.SUCCESS("Демо-дані успішно створено."))

    def seed_categories(self):
        for order, (name, subnames) in enumerate(CATEGORY_TREE):
            parent, _ = Category.objects.get_or_create(
                name=name, parent=None, defaults={"order": order},
            )
            for sub_order, subname in enumerate(subnames):
                Category.objects.get_or_create(
                    name=subname, parent=parent, defaults={"order": sub_order},
                )
        self.stdout.write("Категорії створено.")

    def seed_products(self):
        leaf_categories = list(Category.objects.filter(parent__isnull=False))
        if not leaf_categories:
            return

        counter = 0
        for category in leaf_categories:
            names = PRODUCT_NAMES.get(category.name, [
                f"{category.name} «Старт»",
                f"{category.name} «Урожай»",
                f"{category.name} «Преміум»",
            ])
            descs = SHORT_DESCS.get(category.name, [
                "Якісний товар для саду й городу",
                "Перевірена схожість і склад",
                "Для стабільного результату сезону",
            ])
            for i in range(3):
                counter += 1
                name = names[i % len(names)]
                short = descs[i % len(descs)]
                sku = f"SKU-{counter:04d}"
                product = Product.objects.filter(sku=sku).first()
                if product:
                    product.name = name
                    product.short_description = short
                    product.save(update_fields=["name", "short_description"])
                    continue
                product = Product.objects.create(
                    category=category,
                    sku=sku,
                    name=name,
                    short_description=short,
                    description="Детальний опис товару буде надано замовником після узгодження контенту.",
                    brand=BRANDS[counter % len(BRANDS)],
                    country_of_origin=COUNTRIES[counter % len(COUNTRIES)],
                    base_price=Decimal(str(50 + counter * 3 % 400)),
                    is_own_production=(counter % 4 == 0),
                    is_hit=(counter % 5 == 0),
                    is_new=(counter % 6 == 0),
                    is_sale=(counter % 7 == 0),
                )
                if product.is_sale:
                    product.old_price = product.base_price + Decimal("40")
                    product.save(update_fields=["old_price"])

                for v_order, label in enumerate(["S", "M", "L"]):
                    ProductVariant.objects.create(
                        product=product,
                        label=label,
                        price=product.base_price + Decimal(v_order * 15),
                        old_price=(product.old_price + Decimal(v_order * 15)) if product.old_price else None,
                        stock_qty=0 if (counter % 11 == 0 and v_order == 0) else 10,
                        is_default=(v_order == 0),
                        order=v_order,
                    )
        self.stdout.write(f"Товарів у базі: {Product.objects.count()}.")

    def seed_product_images(self):
        base = Path(__file__).resolve().parents[4] / "static" / "img" / "home"
        pool = []
        for pattern in ("_cand*.jpg", "_c[1-5].jpg", "_s*.jpg", "_t*.jpg", "_pex*.jpg"):
            pool.extend(sorted(base.glob(pattern)))
        pool = [p for p in pool if p.is_file() and p.stat().st_size > 1000]
        if not pool:
            self.stdout.write("Немає зображень для товарів — пропуск.")
            return
        created = 0
        for i, product in enumerate(Product.objects.order_by("id")):
            if product.images.exists():
                continue
            src = pool[i % len(pool)]
            pi = ProductImage(product=product, alt=product.name, order=0)
            with src.open("rb") as fh:
                pi.image.save(f"product-{product.pk}{src.suffix}", File(fh), save=True)
            created += 1
        self.stdout.write(f"Додано фото товарів: {created}.")

    def seed_home_content(self):
        hero_slides = [
            {
                "title": "Якісне насіння для багатого врожаю",
                "lead": "Овочеве, квіткове та вагове насіння з перевіреною схожістю — для саду, городу й розсади.",
                "cta1_text": "До каталогу",
                "cta1_url": "/katalog/nasinnia/",
                "cta2_text": "До акцій",
                "cta2_url": "/katalog/aktsiyi/",
                "order": 0,
            },
            {
                "title": "Овочі з вашої ділянки",
                "lead": "Насіння овочевих культур для свіжих салатів, консервації та сімейного столу весь сезон.",
                "cta1_text": "Обрати насіння",
                "cta1_url": "/katalog/nasinnia/",
                "cta2_text": "До акцій",
                "cta2_url": "/katalog/aktsiyi/",
                "order": 1,
            },
            {
                "title": "Добрива для сильного росту",
                "lead": "Органічні та мінеральні підживлення з перевіреною якістю — для здорових рослин і високого врожаю.",
                "cta1_text": "До добрив",
                "cta1_url": "/katalog/dobriva-ta-stimuliatori-rostu/",
                "cta2_text": "До акцій",
                "cta2_url": "/katalog/aktsiyi/",
                "order": 2,
            },
        ]
        if HeroSlide.objects.count() != len(hero_slides):
            HeroSlide.objects.all().delete()
            for slide in hero_slides:
                HeroSlide.objects.create(eyebrow="", **slide)

        trust_data = [
            ("truck", "Швидка доставка", "Нова Пошта / Укрпошта"),
            ("card", "Оплата онлайн", "LiqPay, післяплата"),
            ("leaf", "Власне виробництво", "Сертифікована якість"),
            ("seed", "Консультація агронома", "Допоможемо з вибором"),
        ]
        for order, (icon, title, text) in enumerate(trust_data):
            HighlightPoint.objects.get_or_create(
                section=HighlightPoint.Section.TRUST, title=title,
                defaults={"icon": icon, "text": text, "order": order},
            )

        info_data = [
            ("truck", "Доставка НП / Укрпоштою", "По всій Україні"),
            ("card", "Оплата онлайн", "Безпечно через LiqPay"),
            ("chat", "Консультація агронома", "Підкажемо, що обрати"),
        ]
        for order, (icon, title, text) in enumerate(info_data):
            HighlightPoint.objects.get_or_create(
                section=HighlightPoint.Section.INFO, title=title,
                defaults={"icon": icon, "text": text, "order": order},
            )

        reviews_data = [
            ("Олена К.", "Замовляла насіння томатів — усе зійшло чудово, якість супер!", 5),
            ("Ігор П.", "Швидка доставка і адекватні ціни. Рекомендую.", 5),
            ("Марина С.", "Дуже задоволена добривами власного виробництва.", 4),
        ]
        for order, (name, text, rating) in enumerate(reviews_data):
            Review.objects.get_or_create(name=name, defaults={"text": text, "rating": rating, "order": order})
        self.stdout.write("Контент головної сторінки створено.")
