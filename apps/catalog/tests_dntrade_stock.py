"""Залишок: пропуск рядка в непорожніх балансах не є явним нулем."""

from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.catalog.dntrade.payload import (
    build_stock_map,
    parse_stock_qty,
    retail_price,
    stock_for,
)
from apps.catalog.models import ProductVariant
from apps.catalog.tests_dntrade_sync import (
    ROOT_ID,
    DntradeManualContentTests,
    _balance,
    _fake_download,
    _row,
    _sync,
)

OTHER_ID = "44444444-5555-6666-7777-888888888888"


class StockContractTests(SimpleTestCase):
    def test_fractional_string_is_not_zero(self):
        self.assertEqual(parse_stock_qty("1.5"), 1)
        self.assertEqual(parse_stock_qty(1.5), 1)
        self.assertEqual(parse_stock_qty(0), 0)
        self.assertEqual(parse_stock_qty("0"), 0)
        self.assertIsNone(parse_stock_qty(None))
        self.assertIsNone(parse_stock_qty(""))
        self.assertIsNone(parse_stock_qty("n/a"))

    def test_negative_stores_clamp_only_the_sum(self):
        class _Balances:
            def iter_balances(self, *, limit=None):
                return iter([{
                    "product_id": "aaa",
                    "stores": [{"balance": "-3"}, {"balance": "5"}],
                }])

        mapped = build_stock_map(_Balances(), limit=None)
        self.assertEqual(mapped["AAA"], 2)

    def test_missing_id_in_nonempty_map_is_unknown(self):
        self.assertIsNone(stock_for({"product_id": "AAA", "balance": 0}, {"BBB": 4}))

    def test_explicit_map_zero_wins_over_payload(self):
        self.assertEqual(stock_for({"product_id": "AAA", "balance": 9}, {"AAA": 0}), 0)

    def test_blank_retail_row_uses_top_level_price(self):
        payload = {
            "prices": [{"price_id": 2, "price_title": "Роздрібна", "price": ""}],
            "price": "19.50",
        }
        self.assertEqual(retail_price(payload), Decimal("19.50"))

    def test_explicit_zero_retail_is_not_replaced(self):
        payload = {
            "prices": [{"price_id": 2, "price_title": "Роздрібна", "price": "0"}],
            "price": "19.50",
        }
        self.assertEqual(retail_price(payload), Decimal("0.00"))


class OmittedBalanceRowTests(TestCase):
    setUp = DntradeManualContentTests.setUp
    _product = DntradeManualContentTests._product

    def _variant(self, product, qty):
        return ProductVariant.objects.create(
            product=product,
            label="мішок",
            sku_variant=product.sku,
            price=Decimal("100.00"),
            stock_qty=qty,
            is_default=True,
            dntrade_product_id=ROOT_ID,
            dntrade_code=20939,
        )

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_missing_row_in_nonempty_balances_keeps_stock_and_content(self, _download):
        product = self._product()
        self._variant(product, 8)
        _sync(
            [
                _row(stock=0, title="Постачальник", price="40.00"),
                _row(
                    product_id=OTHER_ID,
                    sku="99901",
                    code=99901,
                    title="Інший",
                    price="12.00",
                    stock=1,
                ),
            ],
            [_balance(OTHER_ID, 3)],
        )
        product.refresh_from_db()
        variant = product.variants.get()
        self.assertEqual(variant.stock_qty, 8)
        self.assertEqual(variant.label, "мішок")
        self.assertEqual(product.name, "Назва з адмінки")
        self.assertEqual(product.base_price, Decimal("40.00"))

    @patch("apps.catalog.dntrade.images._download_webp", side_effect=_fake_download)
    def test_explicit_zero_balance_row_sets_stock_to_zero(self, _download):
        product = self._product()
        self._variant(product, 8)
        _sync(
            [_row(stock=6, price="40.00", title="інша назва")],
            [_balance(ROOT_ID, 0), _balance(OTHER_ID, 3)],
        )
        product.refresh_from_db()
        self.assertEqual(product.variants.get().stock_qty, 0)
        self.assertEqual(product.name, "Назва з адмінки")
