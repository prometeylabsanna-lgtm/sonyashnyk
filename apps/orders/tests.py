"""Тести Monopay, залишків, checkout, кошика та доступу до замовлення."""

from decimal import Decimal
from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.access import make_order_access_token
from apps.orders.monopay import (
    amount_matches_order,
    amount_to_kopiyky,
    map_status,
    resolve_order_number,
)
from apps.orders.models import Order, OrderItem, PromoCode
from apps.orders.stock import (
    InsufficientStock,
    maybe_expire_order,
    release_order_stock,
    release_stale_monopay_orders,
    reserve_stock_for_items,
)


class MonopayHelpersTests(SimpleTestCase):
    def test_map_status(self):
        self.assertEqual(map_status("success"), "paid")
        self.assertEqual(map_status("failure"), "failed")
        self.assertEqual(map_status("expired"), "failed")
        self.assertEqual(map_status("reversed"), "refunded")
        self.assertIsNone(map_status("processing"))
        self.assertIsNone(map_status("created"))

    def test_amount_matches_order(self):
        order = type("O", (), {"total": Decimal("50.00")})()
        self.assertTrue(amount_matches_order({"amount": 5000, "ccy": 980}, order))
        self.assertTrue(amount_matches_order({"finalAmount": 5000, "amount": 1, "ccy": 980}, order))
        self.assertFalse(amount_matches_order({"amount": 100, "ccy": 980}, order))
        self.assertFalse(amount_matches_order({"amount": 5000, "ccy": 840}, order))
        self.assertEqual(amount_to_kopiyky(Decimal("50.00")), 5000)

    def test_resolve_order_number(self):
        self.assertEqual(resolve_order_number({"reference": "SO-1"}), "SO-1")
        self.assertEqual(
            resolve_order_number({"merchantPaymInfo": {"reference": "SO-2"}}),
            "SO-2",
        )
        self.assertEqual(resolve_order_number({}), "")


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


@override_settings(MONOPAY_TOKEN="", NOVA_POSHTA_API_KEY="")
class CheckoutFlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Каталог", slug="cat-checkout")
        product = Product.objects.create(
            category=cat, sku="SKU-CHK", name="Насіння", base_price=Decimal("50.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="пак", price=Decimal("50.00"), stock_qty=5, is_default=True,
        )
        self.client = Client()

    def _add_to_cart(self, quantity=1):
        return self.client.post(reverse("orders_cart:add"), {
            "variant_id": self.variant.id,
            "quantity": quantity,
        })

    def _checkout_get_token(self):
        response = self.client.get(reverse("orders_checkout:page"))
        self.assertEqual(response.status_code, 200)
        return response.context["checkout_token"]

    def _checkout_post(self, token, **extra):
        data = {
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
            "checkout_token": token,
        }
        data.update(extra)
        return self.client.post(reverse("orders_checkout:page"), data)

    def test_checkout_cod_decrements_stock(self):
        self._add_to_cart()
        token = self._checkout_get_token()
        response = self._checkout_post(token)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertTrue(order.order_number)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 4)

    @override_settings(MONOPAY_TOKEN="test-token")
    @patch("apps.orders.views.monopay.create_invoice")
    def test_monopay_goes_to_pay_redirect(self, mock_create):
        mock_create.return_value = {
            "invoice_id": "inv-1",
            "page_url": "https://pay.mbnk.biz/test",
        }
        self._add_to_cart()
        token = self._checkout_get_token()
        response = self._checkout_post(token, payment_method="monopay")
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertIn(f"/oformlennya/oplata/{order.order_number}/", response["Location"])

        pay_page = self.client.get(response["Location"])
        self.assertEqual(pay_page.status_code, 200)
        self.assertContains(pay_page, "https://pay.mbnk.biz/test")
        mock_create.assert_called_once()
        order.refresh_from_db()
        self.assertEqual(order.monopay_invoice_id, "inv-1")
        self.assertIsNotNone(order.monopay_invoice_at)

    def test_monopay_without_token_redirects_thank_you(self):
        self._add_to_cart()
        token = self._checkout_get_token()
        response = self._checkout_post(token, payment_method="monopay")
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        pay = self.client.get(response["Location"])
        self.assertEqual(pay.status_code, 302)
        self.assertIn(f"/oformlennya/dyakuyemo/{order.order_number}/", pay["Location"])

    def test_double_checkout_same_token(self):
        self._add_to_cart(quantity=2)
        token = self._checkout_get_token()
        first = self._checkout_post(token)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

        # Кошик уже порожній — другий POST не створить замовлення
        self._add_to_cart(quantity=1)
        session = self.client.session
        session["checkout_token"] = token
        session.save()
        second = self._checkout_post(token)
        self.assertEqual(Order.objects.count(), 1)
        self.variant.refresh_from_db()
        # перше замовлення забрало 2; друге не мало списати ще 1
        self.assertEqual(self.variant.stock_qty, 3)

    def test_thank_you_without_access_is_404(self):
        self._add_to_cart()
        token = self._checkout_get_token()
        self._checkout_post(token)
        order = Order.objects.latest("id")
        stranger = Client()
        resp = stranger.get(reverse("orders_checkout:thank_you", args=[order.order_number]))
        self.assertEqual(resp.status_code, 404)

    def test_thank_you_with_token_ok(self):
        self._add_to_cart()
        token = self._checkout_get_token()
        self._checkout_post(token)
        order = Order.objects.latest("id")
        access = make_order_access_token(order.order_number)
        stranger = Client()
        resp = stranger.get(
            reverse("orders_checkout:thank_you", args=[order.order_number]) + f"?t={access}"
        )
        self.assertEqual(resp.status_code, 200)


class CartGuardsTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-cart")
        self.product = Product.objects.create(
            category=cat, sku="SKU-CART", name="Товар", base_price=Decimal("20.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, label="1", price=Decimal("20.00"), stock_qty=0, is_default=True,
        )
        self.client = Client()

    def test_zero_qty_does_not_add_oos(self):
        resp = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.variant.id, "quantity": 0},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_negative_qty_rejected(self):
        resp = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.variant.id, "quantity": -1},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_qty_rejected(self):
        resp = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.variant.id, "quantity": "abc"},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(resp.status_code, 400)

    def test_inactive_product_not_found(self):
        self.variant.stock_qty = 5
        self.variant.save()
        self.product.is_active = False
        self.product.save()
        resp = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.variant.id, "quantity": 1},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(resp.status_code, 404)


class PromoLimitTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-promo")
        product = Product.objects.create(
            category=cat, sku="SKU-PROMO", name="Товар", base_price=Decimal("100.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="1", price=Decimal("100.00"), stock_qty=10, is_default=True,
        )
        self.promo = PromoCode.objects.create(
            code="ONCE",
            discount_type=PromoCode.DiscountType.FIXED,
            amount=Decimal("10.00"),
            max_uses=1,
        )
        self.client = Client()

    def _place(self):
        self.client.post(reverse("orders_cart:add"), {"variant_id": self.variant.id, "quantity": 1})
        self.client.post(reverse("orders_cart:promo"), {"promo_code": "ONCE"})
        page = self.client.get(reverse("orders_checkout:page"))
        token = page.context["checkout_token"]
        return self.client.post(reverse("orders_checkout:page"), {
            "full_name": "Тест",
            "phone": "+380671112233",
            "email": "",
            "delivery_method": "pickup",
            "city": "",
            "warehouse": "",
            "np_city_ref": "",
            "np_warehouse_ref": "",
            "payment_method": "cash_pickup",
            "comment": "",
            "promo_code": "ONCE",
            "agreed_to_data_processing": True,
            "checkout_token": token,
        })

    def test_promo_max_uses(self):
        first = self._place()
        self.assertEqual(first.status_code, 302)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)
        order = Order.objects.latest("id")
        self.assertEqual(order.discount_total, Decimal("10.00"))

        second = self._place()
        self.assertEqual(second.status_code, 302)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)
        order2 = Order.objects.latest("id")
        self.assertEqual(order2.discount_total, Decimal("0"))


@override_settings(MONOPAY_TOKEN="test-token")
class MonopayCallbackTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-cb")
        product = Product.objects.create(
            category=cat, sku="SKU-CB", name="Товар", base_price=Decimal("30.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="1", price=Decimal("30.00"), stock_qty=0, is_default=True,
        )
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380671112233",
            delivery_method=Order.DeliveryMethod.PICKUP,
            payment_method=Order.PaymentMethod.MONOPAY,
            subtotal=Decimal("30.00"),
            total=Decimal("30.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            variant=self.variant,
            product_name=product.name,
            variant_label=self.variant.label,
            price=Decimal("30.00"),
            quantity=1,
        )

    def _post_callback(self, status, amount=3000):
        payload = {
            "invoiceId": "inv-test",
            "status": status,
            "amount": amount,
            "ccy": 980,
            "reference": self.order.order_number,
        }
        body = __import__("json").dumps(payload).encode("utf-8")
        with patch("apps.orders.views.monopay.verify_webhook", return_value=True):
            return self.client.generic(
                "POST",
                reverse("orders_checkout:monopay_callback"),
                data=body,
                content_type="application/json",
                HTTP_X_SIGN="dGVzdA==",
            )

    def test_amount_mismatch_rejected(self):
        resp = self._post_callback("success", amount=100)
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_success_sets_paid(self):
        resp = self._post_callback("success", amount=3000)
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 0)
        self.assertFalse(self.order.stock_released)

    def test_failure_restores_stock(self):
        resp = self._post_callback("failure", amount=3000)
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertTrue(self.order.stock_released)
        self.assertEqual(self.variant.stock_qty, 1)

    def test_failure_idempotent(self):
        self._post_callback("failure", amount=3000)
        self._post_callback("expired", amount=3000)
        self.variant.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 1)
        self.assertTrue(self.order.stock_released)

    def test_reversed_sets_refunded(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        resp = self._post_callback("reversed", amount=3000)
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertTrue(self.order.stock_released)
        self.assertEqual(self.variant.stock_qty, 1)


@override_settings(MONOPAY_STOCK_RESERVE_MINUTES=15)
class StockReleaseTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-rel")
        product = Product.objects.create(
            category=cat, sku="SKU-REL", name="Товар", base_price=Decimal("20.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="1", price=Decimal("20.00"), stock_qty=0, is_default=True,
        )
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380671112233",
            delivery_method=Order.DeliveryMethod.PICKUP,
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal=Decimal("20.00"),
            total=Decimal("20.00"),
            monopay_invoice_id="inv-rel",
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            variant=self.variant,
            product_name=product.name,
            variant_label="1",
            price=Decimal("20.00"),
            quantity=2,
        )

    def test_release_order_stock(self):
        self.assertTrue(release_order_stock(self.order, mark_failed=True))
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertTrue(self.order.stock_released)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.variant.stock_qty, 2)
        self.assertFalse(release_order_stock(self.order))

    def test_stale_pending_releases(self):
        from datetime import timedelta

        from django.utils import timezone

        Order.objects.filter(pk=self.order.pk).update(
            created_at=timezone.now() - timedelta(minutes=16),
            monopay_invoice_at=timezone.now() - timedelta(minutes=16),
        )
        self.order.refresh_from_db()
        self.assertEqual(release_stale_monopay_orders(minutes=15), 1)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertTrue(self.order.stock_released)
        self.assertEqual(self.variant.stock_qty, 2)

    def test_fresh_pending_not_expired(self):
        self.assertFalse(maybe_expire_order(self.order))
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 0)

    def test_rereserve_after_release(self):
        from apps.orders.stock import rereserve_order_stock

        release_order_stock(self.order, mark_failed=True)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 2)
        rereserve_order_stock(self.order)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertFalse(self.order.stock_released)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.variant.stock_qty, 0)

    @patch("apps.orders.monopay.get_invoice_status")
    @patch("apps.orders.monopay.is_configured", return_value=True)
    def test_sync_expired_releases_stock(self, _cfg, mock_status):
        from apps.orders.stock import sync_order_from_monopay

        mock_status.return_value = {
            "invoiceId": "inv-rel",
            "status": "expired",
            "amount": 2000,
            "ccy": 980,
        }
        self.assertTrue(sync_order_from_monopay(self.order))
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertTrue(self.order.stock_released)
        self.assertEqual(self.variant.stock_qty, 2)


class ZeroPriceAndLimitTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-zero")
        self.free = Product.objects.create(
            category=cat, sku="SKU-FREE", name="Безкоштовний", base_price=Decimal("0"),
        )
        self.free_v = ProductVariant.objects.create(
            product=self.free, label="1", price=Decimal("0"), stock_qty=5, is_default=True,
        )
        self.client = Client()

    def test_zero_price_rejected(self):
        resp = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.free_v.id, "quantity": 1},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.client.session.get("cart", {}), {})


class PaymentStatusEndpointTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-st")
        product = Product.objects.create(
            category=cat, sku="SKU-ST", name="Товар", base_price=Decimal("10.00"),
        )
        ProductVariant.objects.create(
            product=product, label="1", price=Decimal("10.00"), stock_qty=1, is_default=True,
        )
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380671112233",
            delivery_method=Order.DeliveryMethod.PICKUP,
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal=Decimal("10.00"),
            total=Decimal("10.00"),
        )
        self.client = Client()

    def test_status_without_access_404(self):
        resp = self.client.get(
            reverse("orders_checkout:payment_status", args=[self.order.order_number])
        )
        self.assertEqual(resp.status_code, 404)

    def test_status_with_token(self):
        access = make_order_access_token(self.order.order_number)
        resp = self.client.get(
            reverse("orders_checkout:payment_status", args=[self.order.order_number])
            + f"?t={access}"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["payment_status"], "pending")


class NpWarehouseValidateTests(TestCase):
    @override_settings(NOVA_POSHTA_API_KEY="test-key")
    @patch("apps.orders.forms.warehouse_exists", return_value=False)
    def test_form_rejects_stale_warehouse(self, _mock):
        from apps.orders.forms import CheckoutForm

        form = CheckoutForm(data={
            "full_name": "Тест",
            "phone": "+380671112233",
            "email": "",
            "delivery_method": "np_branch",
            "city": "Київ",
            "warehouse": "Відділення 1",
            "np_city_ref": "city-ref",
            "np_warehouse_ref": "wh-ref-gone",
            "payment_method": "cod",
            "comment": "",
            "promo_code": "",
            "agreed_to_data_processing": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("warehouse", form.errors)
