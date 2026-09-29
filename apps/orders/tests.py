"""Тести LiqPay, залишків, checkout, кошика та доступу до замовлення."""

from decimal import Decimal
from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.access import make_order_access_token
from apps.orders.liqpay import (
    amount_matches_order,
    encode_data,
    map_status,
    sign_data,
    verify_signature,
)
from apps.orders.models import Order, PromoCode
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
        self.assertEqual(map_status("reversed"), "refunded")
        self.assertIsNone(map_status("processing"))

    def test_amount_matches_order(self):
        order = type("O", (), {"total": Decimal("50.00")})()
        self.assertTrue(amount_matches_order({"amount": "50.00", "currency": "UAH"}, order))
        self.assertFalse(amount_matches_order({"amount": "1.00", "currency": "UAH"}, order))
        self.assertFalse(amount_matches_order({"amount": "50.00", "currency": "USD"}, order))


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


@override_settings(LIQPAY_PUBLIC_KEY="", LIQPAY_PRIVATE_KEY="", NOVA_POSHTA_API_KEY="", LIQPAY_ALLOW_MOCK=True)
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

    def test_liqpay_goes_to_mock_pay(self):
        self._add_to_cart()
        token = self._checkout_get_token()
        response = self._checkout_post(token, payment_method="liqpay")
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertIn(f"/oformlennya/oplata/{order.order_number}/", response["Location"])

        mock_page = self.client.get(response["Location"])
        self.assertEqual(mock_page.status_code, 200)
        self.assertContains(mock_page, "Sandbox-оплата")

        access = make_order_access_token(order.order_number)
        fail = self.client.post(
            reverse("orders_checkout:pay_mock", args=[order.order_number]) + f"?t={access}",
            {"action": "fail"},
        )
        self.assertEqual(fail.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)

        thank = self.client.get(fail["Location"])
        self.assertEqual(thank.status_code, 200)

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


@override_settings(LIQPAY_PUBLIC_KEY="", LIQPAY_PRIVATE_KEY="", LIQPAY_ALLOW_MOCK=False)
class PayMockDisabledTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-mock-off")
        product = Product.objects.create(
            category=cat, sku="SKU-MOCK", name="Товар", base_price=Decimal("10.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=product, label="1", price=Decimal("10.00"), stock_qty=3, is_default=True,
        )
        self.client = Client()
        self.client.post(reverse("orders_cart:add"), {"variant_id": self.variant.id, "quantity": 1})
        page = self.client.get(reverse("orders_checkout:page"))
        token = page.context["checkout_token"]
        self.client.post(reverse("orders_checkout:page"), {
            "full_name": "Тест",
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
            "checkout_token": token,
        })
        self.order = Order.objects.latest("id")

    def test_pay_mock_404_when_disabled(self):
        access = make_order_access_token(self.order.order_number)
        session = self.client.session
        session["last_order_number"] = self.order.order_number
        session.save()
        resp = self.client.get(
            reverse("orders_checkout:pay", args=[self.order.order_number]) + f"?t={access}"
        )
        self.assertEqual(resp.status_code, 404)
        post = self.client.post(
            reverse("orders_checkout:pay_mock", args=[self.order.order_number]) + f"?t={access}",
            {"action": "success"},
        )
        self.assertEqual(post.status_code, 404)


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


@override_settings(LIQPAY_PRIVATE_KEY="secret")
class LiqPayCallbackTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-cb")
        product = Product.objects.create(
            category=cat, sku="SKU-CB", name="Товар", base_price=Decimal("30.00"),
        )
        ProductVariant.objects.create(
            product=product, label="1", price=Decimal("30.00"), stock_qty=1, is_default=True,
        )
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380671112233",
            delivery_method=Order.DeliveryMethod.PICKUP,
            payment_method=Order.PaymentMethod.LIQPAY,
            subtotal=Decimal("30.00"),
            total=Decimal("30.00"),
        )

    def _post_callback(self, status, amount="30.00"):
        payload = {
            "order_id": self.order.order_number,
            "status": status,
            "amount": amount,
            "currency": "UAH",
        }
        data = encode_data(payload)
        signature = sign_data(data, "secret")
        return self.client.post(
            reverse("orders_checkout:liqpay_callback"),
            {"data": data, "signature": signature},
        )

    def test_amount_mismatch_rejected(self):
        resp = self._post_callback("success", amount="1.00")
        self.assertEqual(resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_success_sets_paid(self):
        resp = self._post_callback("success", amount="30.00")
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_reversed_sets_refunded(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        resp = self._post_callback("reversed", amount="30.00")
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)


class ZeroPriceAndLimitTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-zero")
        self.free = Product.objects.create(
            category=cat, sku="SKU-FREE", name="Безкоштовний", base_price=Decimal("0"),
        )
        self.free_v = ProductVariant.objects.create(
            product=self.free, label="1", price=Decimal("0"), stock_qty=5, is_default=True,
        )
        self.limited = Product.objects.create(
            category=cat, sku="SKU-LIM", name="Ліміт", base_price=Decimal("50.00"),
        )
        self.limited_v = ProductVariant.objects.create(
            product=self.limited, label="1", price=Decimal("50.00"), stock_qty=10,
            max_per_order=2, is_default=True,
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

    def test_max_per_order_enforced(self):
        ok = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.limited_v.id, "quantity": 2},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(ok.status_code, 200)
        over = self.client.post(
            reverse("orders_cart:add"),
            {"variant_id": self.limited_v.id, "quantity": 1},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(over.status_code, 400)
        self.assertEqual(self.client.session["cart"][str(self.limited_v.id)], 2)


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
            payment_method=Order.PaymentMethod.LIQPAY,
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
