"""--purge-missing ховає відсутні товари і не видаляє кураторські дані."""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.catalog.models import Product, ProductVariant
from apps.catalog.tests_dntrade_sync import (
    ROOT_ID,
    DntradeManualContentTests,
    _balance,
    _fake_download,
    _row,
    _sync,
)

OTHER_ID = "33333333-4444-5555-6666-777777777777"


class MissingFeedHideTests(TestCase):
    setUp = DntradeManualContentTests.setUp
    _product = DntradeManualContentTests._product
    _photo = DntradeManualContentTests._photo

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_partial_feed_keeps_missing_curated_row_and_photos(self, _download):
        curated = self._product()
        photo = self._photo(curated)
        ProductVariant.objects.create(
            product=curated,
            label="мішок",
            sku_variant="20939",
            price=Decimal("100.00"),
            stock_qty=2,
            is_default=True,
            dntrade_product_id=ROOT_ID,
            dntrade_code=20939,
        )
        manual = Product.objects.create(
            category=self.manual,
            sku="MANUAL-1",
            name="Лише ручний",
            base_price="10.00",
        )
        stats = _sync(
            [_row(
                product_id=OTHER_ID,
                sku="99901",
                code=99901,
                title="Інший у фіді",
                price="12.00",
                stock=1,
            )],
            [_balance(OTHER_ID, 1)],
            purge_missing=True,
        )
        curated.refresh_from_db()
        self.assertEqual(stats.purged, 1)
        self.assertTrue(Product.objects.filter(pk=curated.pk).exists())
        self.assertFalse(curated.is_active)
        self.assertEqual(curated.name, "Назва з адмінки")
        self.assertEqual(curated.description, "<p>Повний опис редактора</p>")
        self.assertEqual(curated.pack_volume, "10 шт")
        self.assertEqual(curated.images.get().pk, photo.pk)
        self.assertEqual(curated.variants.get().label, "мішок")
        self.assertEqual(curated.variants.get().stock_qty, 2)
        self.assertTrue(Product.objects.get(pk=manual.pk).is_active)

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_reappearance_restores_availability_without_overwriting_content(self, _download):
        curated = self._product()
        photo = self._photo(curated)
        ProductVariant.objects.create(
            product=curated,
            label="мішок",
            sku_variant="20939",
            price=Decimal("100.00"),
            stock_qty=2,
            is_default=True,
            dntrade_product_id=ROOT_ID,
            dntrade_code=20939,
        )
        _sync(
            [_row(
                product_id=OTHER_ID,
                sku="99901",
                code=99901,
                title="Інший у фіді",
                price="12.00",
                stock=1,
            )],
            [_balance(OTHER_ID, 1)],
            purge_missing=True,
        )
        _sync(
            [_row(
                title="З фіда знову",
                short="",
                description="",
                unit="шт",
                price="55.00",
                stock=4,
                status=1,
                image="https://cdn.example.test/back.jpg",
            )],
            [_balance(ROOT_ID, 4)],
            purge_missing=True,
        )
        curated.refresh_from_db()
        variant = curated.variants.get()
        self.assertTrue(curated.is_active)
        self.assertEqual(curated.name, "Назва з адмінки")
        self.assertEqual(curated.short_description, "Коротко від редактора")
        self.assertEqual(curated.description, "<p>Повний опис редактора</p>")
        self.assertEqual(curated.pack_volume, "10 шт")
        self.assertEqual(curated.category_id, self.manual.pk)
        self.assertEqual(curated.base_price, Decimal("55.00"))
        self.assertEqual(variant.label, "мішок")
        self.assertEqual(variant.stock_qty, 4)
        self.assertEqual(curated.images.get().pk, photo.pk)
        self.assertEqual(curated.images.get().alt, "ручне фото")
