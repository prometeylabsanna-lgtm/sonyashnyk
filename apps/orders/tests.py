"""Тести LiqPay підпису, залишків і checkout-флоу (mock)."""

from decimal import Decimal

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.liqpay import encode_data, map_status, sign_data, verify_signature
from apps.orders.models import Order
from apps.orders.stock import InsufficientStock, reserve_stock_for_items


class LiqPayHelpersTests(SimpleTestCase):
    def test_sign_and_verify(self):
        with self.settings(LIQPAY_PRIVATE_KEY="test_private"):
            data = encode_data({"order_id": "1", "amount": "10"})
            signature = sign_data(data, "test_private")
            self.assertTrue(verify_signature(data, signature))
            self.assertFalse(verify_signature(data, "bad"))

    def test_map_status(self):
        self.assertEqual(map_status("success"), "paid")
        self.assertEqual(map_status("failure"), "failed")
        self.assertIsNone(map_status("processing"))


class StockTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Тест", slug="test-stock")
        product = Product.objects.create(
            category=cat, sku="SKU-1", name="Товар", base_price=Decimal("100.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="1 шт", price=Decimal("100.00"), stock_qty=2,
        )

    def test_decrement(self):
        reserve_stock_for_items([{"variant": self.variant, "quantity": 2}])
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 0)

    def test_insufficient(self):
        with self.assertRaises(InsufficientStock):
            reserve_stock_for_items([{"variant": self.variant, "quantity": 5}])


@override_settings(LIQPAY_PUBLIC_KEY="", LIQPAY_PRIVATE_KEY="", NOVA_POSHTA_API_KEY="")
class CheckoutMockFlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Каталог", slug="cat-checkout")
        product = Product.objects.create(
            category=cat, sku="SKU-CHK", name="Насіння", base_price=Decimal("50.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="пак", price=Decimal("50.00"), stock_qty=5, is_default=True,
        )
        self.client = Client()

    def _add_to_cart(self):
        return self.client.post(reverse("orders_cart:add"), {
            "variant_id": self.variant.id,
            "quantity": 1,
        })

    def test_checkout_cod_decrements_stock(self):
        self._add_to_cart()
        response = self.client.post(reverse("orders_checkout:page"), {
            "full_name": "Тест Користувач",
            "phone": "+380671112233",
            "email": "",
            "delivery_method": "pickup",
            "city": "",
            "warehouse": "",
            "np_city_ref": "",
            "np_warehouse_ref": "",
            "payment_method": "cash_pickup",
            "comment": "",
            "promo_code": "",
            "agreed_to_data_processing": True,
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertTrue(order.order_number)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 4)

    def test_liqpay_goes_to_mock_pay(self):
        self._add_to_cart()
        response = self.client.post(reverse("orders_checkout:page"), {
            "full_name": "Тест Користувач",
            "phone": "+380671112233",
            "email": "",
            "delivery_method": "pickup",
            "city": "",
            "warehouse": "",
            "np_city_ref": "",
            "np_warehouse_ref": "",
            "payment_method": "liqpay",
            "comment": "",
            "promo_code": "",
            "agreed_to_data_processing": True,
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertIn(f"/oformlennya/oplata/{order.order_number}/", response["Location"])

        mock_page = self.client.get(reverse("orders_checkout:pay", args=[order.order_number]))
        self.assertEqual(mock_page.status_code, 200)
        self.assertContains(mock_page, "Sandbox-оплата")

        fail = self.client.post(
            reverse("orders_checkout:pay_mock", args=[order.order_number]),
            {"action": "fail"},
        )
        self.assertEqual(fail.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)

        thank = self.client.get(reverse("orders_checkout:thank_you", args=[order.order_number]))
        self.assertContains(thank, "Сплатити ще раз")
