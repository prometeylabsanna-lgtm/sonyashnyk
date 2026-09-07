"""Наповнює БД тестовими (placeholder) даними для перевірки шаблонів.

Використання: python3 manage.py seed_demo
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductVariant
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


class Command(BaseCommand):
    help = "Наповнює БД демо-даними (категорії, товари, банери) для перевірки верстки."

    def handle(self, *args, **options):
        self.seed_categories()
        self.seed_products()
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
            for i in range(3):
                counter += 1
                name = f"{category.name} — товар {i + 1}"
                sku = f"SKU-{counter:04d}"
                if Product.objects.filter(sku=sku).exists():
                    continue
                product = Product.objects.create(
                    category=category,
                    sku=sku,
                    name=name,
                    short_description="Опис товару буде додано пізніше.",
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

    def seed_home_content(self):
        if not HeroSlide.objects.exists():
            HeroSlide.objects.create(
                eyebrow="Сезон почався",
                title="Насіння, добрива та все для саду й городу",
                lead="Понад 1000 товарів: власне виробництво, сертифікована якість, швидка доставка по всій Україні.",
                order=0,
            )
            HeroSlide.objects.create(
                eyebrow="Власне виробництво",
                title="Сертифікована якість від «Соняшник»",
                lead="Перевірені насіння та добрива власного виробництва з підтвердженням якості.",
                cta1_text="Сертифікати",
                cta1_url="/sertyfikaty/",
                order=1,
            )

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
            ("phone", "Консультація агронома", "Підкажемо, що обрати"),
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
