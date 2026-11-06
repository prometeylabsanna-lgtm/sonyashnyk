"""Короткий опис товару видимий на сторінці, окремо від повного опису."""

from decimal import Decimal
from pathlib import Path

from django.test import Client, TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant

CSS_PATH = Path(__file__).resolve().parents[2] / "static" / "css" / "product.css"


def _product(**kwargs):
    category = Category.objects.create(name="Насіння", slug="nasinnia-pdp")
    data = {
        "category": category,
        "sku": "PDP-1",
        "name": "Назва UA",
        "name_ru": "Название RU",
        "slug": "pdp-short",
        "base_price": Decimal("25.00"),
        "is_active": True,
    }
    data.update(kwargs)
    product = Product.objects.create(**data)
    ProductVariant.objects.create(
        product=product,
        label="10 шт",
        price=Decimal("25.00"),
        stock_qty=4,
        is_default=True,
    )
    return product


class ProductShortDescriptionTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _page(self, lang="uk"):
        self.client.cookies["sonyashnyk_lang"] = lang
        return self.client.get(reverse("product_detail", kwargs={"slug": "pdp-short"}))

    def test_populated_uk_shows_short_once_and_keeps_full_description(self):
        _product(
            short_description="Коротко про товар",
            short_description_ru="Кратко о товаре",
            description="<p>Повний опис з <strong>акцентом</strong></p>",
            description_ru="<p>Полное описание</p>",
        )
        response = self._page("uk")
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html.count("Коротко про товар"), 2)  # lead + meta description
        self.assertIn('class="pdp-info__lead"', html)
        self.assertIn("<strong>акцентом</strong>", html)
        self.assertNotIn("Кратко о товаре", html)
        self.assertNotIn("Полное описание", html)

    def test_empty_short_renders_no_lead(self):
        _product(short_description="", description="<p>Лише повний</p>")
        html = self._page("uk").content.decode()
        self.assertNotIn("pdp-info__lead", html)
        self.assertIn("Лише повний", html)

    def test_short_without_description_is_not_repeated_as_body(self):
        _product(short_description="Тільки короткий", description="")
        html = self._page("uk").content.decode()
        self.assertEqual(html.count("Тільки короткий"), 2)  # lead + meta
        self.assertNotIn("pdp-desc__body", html)

    def test_ru_uses_ru_short_and_falls_back_when_empty(self):
        _product(
            short_description="Коротко UA",
            short_description_ru="Кратко RU",
            description="<p>Повний UA</p>",
            description_ru="<p>Полный RU</p>",
        )
        ru = self._page("ru").content.decode()
        self.assertIn("Кратко RU", ru)
        self.assertNotIn("Коротко UA", ru)
        self.assertIn("Полный RU", ru)

        product = Product.objects.get(slug="pdp-short")
        product.short_description_ru = ""
        product.save(update_fields=["short_description_ru"])
        fallback = self._page("ru").content.decode()
        self.assertIn("Коротко UA", fallback)

    def test_short_description_is_escaped(self):
        _product(short_description='<script>alert("x")</script>', description="<p>Ок</p>")
        html = self._page("uk").content.decode()
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_lead_css_covers_desktop_tablet_and_mobile(self):
        css = CSS_PATH.read_text(encoding="utf-8")
        self.assertIn(".pdp-info__lead", css)
        tablet = css.split("/* --- Планшет --- */", 1)[1].split("/* --- Мобільний", 1)[0]
        mobile = css.split("/* --- Мобільний", 1)[1]
        self.assertIn(".pdp-info__lead", tablet)
        self.assertIn(".pdp-info__lead", mobile)
        self.assertNotIn("!important", css[css.find(".pdp-info__lead"):css.find(".pdp-info__lead") + 400])
