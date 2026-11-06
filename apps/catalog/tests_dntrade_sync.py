"""Регресія: синк DNTrade не затирає ручний контент і фото наявних товарів."""

from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase
from PIL import Image

from apps.catalog.dntrade.images import sync_product_images
from apps.catalog.dntrade.sync import sync_catalog
from apps.catalog.filter_models import CatalogFilter, CatalogFilterValue, ProductAttribute
from apps.catalog.forms import ProductAdminForm
from apps.catalog.models import Category, Product, ProductImage, ProductVariant

ROOT_ID = "11111111-2222-3333-4444-555555555555"
CHILD_ID = "22222222-3333-4444-5555-666666666666"


def _tiny_webp(name="photo.webp"):
    buf = BytesIO()
    Image.new("RGB", (2, 2), (20, 40, 60)).save(buf, format="WEBP")
    return ContentFile(buf.getvalue(), name=name)


def _fake_download(url, sku, order):
    return _tiny_webp(f"{sku}-{order}.webp")


class _Feed:
    def __init__(self, products, balances=None):
        self.products = list(products)
        self.balances = list(balances or [])

    def iter_products(self, *, store_id=None, limit=None, offset=0):
        rows = self.products[offset:]
        if limit is not None:
            rows = rows[:limit]
        return iter(rows)

    def iter_balances(self, *, limit=None):
        rows = self.balances
        if limit is not None:
            rows = rows[:limit]
        return iter(rows)


def _balance(product_id, qty):
    return {"product_id": product_id, "stores": [{"balance": qty}]}


def _row(
    *,
    product_id=ROOT_ID,
    sku="20939",
    code=20939,
    title="Назва постачальника",
    price="50.00",
    stock=1,
    status=1,
    short="",
    description="",
    unit="шт",
    category="Добрива",
    image="https://cdn.example.test/supplier.jpg",
    include_price=True,
    include_status=True,
    parent_id="",
):
    row = {
        "product_id": product_id,
        "code": code,
        "sku": sku,
        "title": title,
        "short_description": short,
        "description": description,
        "unit_title": unit,
        "category": {"title": category} if category else {},
        "image_path": image,
        "images": [image] if image else [],
        "balance": stock,
    }
    if parent_id:
        row["parent_id"] = parent_id
    if include_status:
        row["status"] = status
    if include_price:
        row["price"] = price
        row["prices"] = [{
            "price_id": 2,
            "price_title": "Роздрібна",
            "price": price,
        }]
    return row


def _sync(products, balances=None, **kwargs):
    return sync_catalog(
        client=_Feed(products, balances),
        dry_run=False,
        skip_images=False,
        purge_missing=kwargs.get("purge_missing", False),
    )


def _ensure_choice(slug, name, value):
    catalog_filter, _ = CatalogFilter.objects.get_or_create(
        slug=slug,
        defaults={"name": name, "is_active": True},
    )
    CatalogFilterValue.objects.get_or_create(
        catalog_filter=catalog_filter,
        value=value,
        defaults={"is_active": True},
    )


class DntradeManualContentTests(TestCase):
    def setUp(self):
        self.manual = Category.objects.create(name="Редакційна", slug="redaktsiina")
        self.supplier_cat = Category.objects.create(name="Добрива", slug="dobryva-sync")
        self.seeds = Category.objects.create(name="Насіння", slug="nasinnia-sync")

    def _product(self, **kwargs):
        data = {
            "category": self.manual,
            "sku": "20939",
            "name": "Назва з адмінки",
            "short_description": "Коротко від редактора",
            "description": "<p>Повний опис редактора</p>",
            "description_ru": "Опис RU",
            "name_ru": "Название RU",
            "pack_volume": "10 шт",
            "brand": "Редакторський бренд",
            "country_of_origin": "Україна",
            "characteristics": {"Склад": "насіння"},
            "base_price": Decimal("100.00"),
            "old_price": Decimal("120.00"),
            "is_active": True,
            "dntrade_product_id": ROOT_ID,
            "dntrade_code": 20939,
        }
        data.update(kwargs)
        return Product.objects.create(**data)

    def _photo(self, product):
        buf = BytesIO()
        Image.new("RGB", (3, 3), (200, 10, 10)).save(buf, format="PNG")
        return ProductImage.objects.create(
            product=product,
            image=ContentFile(buf.getvalue(), name="manual.png"),
            source_url="https://cdn.example.test/manual-old.jpg",
            alt="ручне фото",
            order=0,
        )

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_new_import_sets_content_price_stock_and_photo(self, _download):
        stats = _sync(
            [_row(
                sku="23294",
                code=23294,
                title="Нове насіння",
                short="коротко з фіда",
                description="повний опис фіда",
                unit="5 шт",
                category="Насіння",
                price="77.25",
                stock=6,
            )],
            [_balance(ROOT_ID, 6)],
        )
        product = Product.objects.get(sku="23294")
        self.assertEqual(stats.products_created, 1)
        self.assertEqual(product.name, "Нове насіння")
        self.assertEqual(product.short_description, "коротко з фіда")
        self.assertEqual(product.description, "повний опис фіда")
        self.assertEqual(product.pack_volume, "5 шт")
        self.assertEqual(product.category_id, self.seeds.pk)
        self.assertEqual(product.base_price, Decimal("77.25"))
        self.assertEqual(product.variants.get().price, Decimal("77.25"))
        self.assertEqual(product.variants.get().stock_qty, 6)
        self.assertEqual(product.images.count(), 1)
        self.assertEqual(stats.images_downloaded, 1)

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_admin_edit_then_repeated_sync_keeps_content_and_photos(self, _download):
        _ensure_choice("brand", "Бренд", "Редакторський бренд")
        _ensure_choice("country", "Країна", "Україна")
        _ensure_choice("pieces", "Кількість шт", "10 шт")
        product = self._product(
            name="Сира назва",
            short_description="сирий",
            description="сирий опис",
            pack_volume="шт",
            brand="",
            country_of_origin="",
            characteristics={},
            category=self.supplier_cat,
        )
        ProductVariant.objects.create(
            product=product,
            label="старий",
            sku_variant="20939",
            price=Decimal("100.00"),
            stock_qty=2,
            is_default=True,
            dntrade_product_id=ROOT_ID,
            dntrade_code=20939,
        )
        form = ProductAdminForm({
            "category": str(self.manual.pk),
            "sku": "20939",
            "name": "Назва з адмінки",
            "slug": product.slug,
            "base_price": "100.00",
            "old_price": "120.00",
            "short_description": "Коротко від редактора",
            "description": "<p>Повний опис редактора</p>",
            "name_ru": "Название RU",
            "description_ru": "Опис RU",
            "dntrade_product_id": ROOT_ID,
            "dntrade_code": "20939",
            "is_active": "on",
            "characteristics_key": ["Склад"],
            "characteristics_value": ["насіння"],
            "characteristics_ru_key": ["Состав"],
            "characteristics_ru_value": ["семена"],
            "attr_brand": "Редакторський бренд",
            "attr_country": "Україна",
            "attr_pieces": "10 шт",
            "attr_volume": "",
            "attr_weight": "",
        }, instance=product)
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        photo = self._photo(product)
        variant = product.variants.get()
        variant.label = "мішок"
        variant.save(update_fields=["label"])

        hostile = dict(
            title="ЗНОВУ ПОСТАЧАЛЬНИК",
            short="",
            description="",
            unit="шт",
            category="Добрива",
            image="https://cdn.example.test/replacement.jpg",
        )
        for price, stock in (("111.00", 4), ("222.50", 9)):
            stats = _sync(
                [_row(price=price, stock=stock, **hostile)],
                [_balance(ROOT_ID, stock)],
            )
            self.assertEqual(stats.products_updated, 1)
            self.assertEqual(stats.products_created, 0)
            self.assertEqual(stats.images_downloaded, 0)

        product.refresh_from_db()
        variant.refresh_from_db()
        self.assertEqual(product.name, "Назва з адмінки")
        self.assertEqual(product.short_description, "Коротко від редактора")
        self.assertEqual(product.description, "<p>Повний опис редактора</p>")
        self.assertEqual(product.description_ru, "Опис RU")
        self.assertEqual(product.name_ru, "Название RU")
        self.assertEqual(product.pack_volume, "10 шт")
        self.assertEqual(product.category_id, self.manual.pk)
        self.assertEqual(product.brand, "Редакторський бренд")
        self.assertEqual(product.country_of_origin, "Україна")
        self.assertEqual(product.characteristics, {"Склад": "насіння"})
        self.assertEqual(product.characteristics_ru, {"Состав": "семена"})
        self.assertEqual(product.old_price, Decimal("120.00"))
        self.assertEqual(product.base_price, Decimal("222.50"))
        self.assertEqual(variant.label, "мішок")
        self.assertEqual(variant.price, Decimal("222.50"))
        self.assertEqual(variant.stock_qty, 9)
        self.assertTrue(product.is_active)
        saved = ProductImage.objects.get(pk=photo.pk)
        self.assertEqual(saved.alt, "ручне фото")
        self.assertEqual(saved.source_url, "https://cdn.example.test/manual-old.jpg")
        self.assertEqual(product.images.count(), 1)
        self.assertEqual(
            ProductAttribute.objects.get(
                product=product,
                catalog_filter__slug="brand",
            ).value,
            "Редакторський бренд",
        )

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_blank_supplier_does_not_wipe_content_price_or_photos(self, _download):
        product = self._product(sku="63280", dntrade_code=63280)
        photo = self._photo(product)
        ProductVariant.objects.create(
            product=product,
            label="10 шт",
            sku_variant="63280",
            price=Decimal("100.00"),
            stock_qty=2,
            is_default=True,
            dntrade_product_id=ROOT_ID,
        )
        stats = _sync(
            [_row(
                sku="63280",
                code=63280,
                title="",
                short="",
                description="",
                unit="",
                category="",
                image="",
                include_price=False,
                include_status=False,
                stock=0,
            )],
            [_balance(ROOT_ID, 15)],
        )
        product.refresh_from_db()
        self.assertEqual(stats.products_updated, 1)
        self.assertEqual(product.name, "Назва з адмінки")
        self.assertEqual(product.short_description, "Коротко від редактора")
        self.assertEqual(product.description, "<p>Повний опис редактора</p>")
        self.assertEqual(product.pack_volume, "10 шт")
        self.assertEqual(product.category_id, self.manual.pk)
        self.assertEqual(product.base_price, Decimal("100.00"))
        self.assertTrue(product.is_active)
        self.assertEqual(product.variants.get().stock_qty, 15)
        self.assertEqual(product.variants.get().label, "10 шт")
        self.assertEqual(product.images.get().pk, photo.pk)
        self.assertEqual(stats.images_downloaded, 0)

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_deliberate_clear_is_not_refilled(self, _download):
        product = self._product(
            sku="853",
            dntrade_code=853,
            short_description="",
            description="",
            pack_volume="",
        )
        ProductVariant.objects.create(
            product=product,
            label="1 шт",
            sku_variant="853",
            price=Decimal("100.00"),
            stock_qty=1,
            is_default=True,
            dntrade_product_id=ROOT_ID,
        )
        _sync(
            [_row(
                sku="853",
                code=853,
                title="Повернути назву постачальника",
                short="коротко з фіда",
                description="опис, який адмін стер",
                unit="шт",
                price="40.00",
                stock=3,
                image="https://cdn.example.test/should-not-return.jpg",
            )],
            [_balance(ROOT_ID, 3)],
        )
        product.refresh_from_db()
        self.assertEqual(product.name, "Назва з адмінки")
        self.assertEqual(product.short_description, "")
        self.assertEqual(product.description, "")
        self.assertEqual(product.pack_volume, "")
        self.assertEqual(product.images.count(), 0)
        self.assertEqual(product.base_price, Decimal("40.00"))
        self.assertEqual(product.variants.get().stock_qty, 3)

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_explicit_inactive_status_still_applies(self, _download):
        product = self._product(sku="23537", dntrade_code=23537)
        ProductVariant.objects.create(
            product=product,
            label="10 шт",
            sku_variant="23537",
            price=Decimal("100.00"),
            stock_qty=1,
            is_default=True,
            dntrade_product_id=ROOT_ID,
        )
        _sync(
            [_row(sku="23537", code=23537, status=0, price="15.00", stock=0, title="інша")],
            [_balance(ROOT_ID, 0)],
        )
        product.refresh_from_db()
        self.assertFalse(product.is_active)
        self.assertEqual(product.name, "Назва з адмінки")
        self.assertEqual(product.base_price, Decimal("15.00"))
        self.assertEqual(product.variants.get().stock_qty, 0)

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_existing_variant_label_survives_child_row(self, _download):
        product = self._product()
        variant = ProductVariant.objects.create(
            product=product,
            label="мішок",
            sku_variant="20939-5",
            price=Decimal("100.00"),
            stock_qty=1,
            is_default=True,
            dntrade_product_id=CHILD_ID,
            dntrade_code=209395,
        )
        child = _row(
            product_id=CHILD_ID,
            sku="20939-5",
            code=209395,
            title="Фасування постачальника 5 кг",
            unit="5 кг",
            price="64.00",
            stock=8,
            parent_id=ROOT_ID,
        )
        root = _row(title="Батько з фіда", price="10.00", stock=1)
        _sync([root, child], [_balance(ROOT_ID, 1), _balance(CHILD_ID, 8)])
        variant.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(variant.label, "мішок")
        self.assertEqual(variant.price, Decimal("64.00"))
        self.assertEqual(variant.stock_qty, 8)
        self.assertEqual(product.name, "Назва з адмінки")

    def test_empty_feed_does_not_purge_catalog(self):
        product = self._product(sku="8341", dntrade_code=8341)
        stats = _sync([], [], purge_missing=True)
        self.assertEqual(stats.purged, 0)
        self.assertTrue(any("0 товарів" in err for err in stats.errors))
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_image_sync_keeps_gallery_on_blank_or_different_urls(self):
        product = self._product(sku="23530", dntrade_code=23530)
        photo = self._photo(product)
        self.assertEqual(sync_product_images(product, {"image_path": "", "images": []}), 0)
        self.assertEqual(
            sync_product_images(
                product,
                {"image_path": "https://cdn.example.test/other.jpg", "images": []},
            ),
            0,
        )
        self.assertEqual(product.images.get().pk, photo.pk)
        self.assertEqual(product.images.get().alt, "ручне фото")
