from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.catalog.models import Category, Product


class ProductAdminOpenTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            "product-admin",
            "product-admin@example.com",
            "test-pass-123",
        )
        self.client = Client()
        self.client.force_login(user)
        self.category = Category.objects.create(name="Тест", slug="test-admin-cat")
        self.product = Product.objects.create(
            category=self.category,
            sku="ADM-1",
            name="Товар адмінки",
            slug="tovar-admin",
            base_price="10.00",
        )

    def test_add_and_change_pages_open(self):
        add = self.client.get("/admin/catalog/product/add/")
        change = self.client.get(f"/admin/catalog/product/{self.product.pk}/change/")
        self.assertEqual(add.status_code, 200)
        self.assertEqual(change.status_code, 200)
        self.assertContains(change, "attr_")
        self.assertContains(change, 'data-char-kv-name="characteristics"')
        self.assertContains(change, 'data-char-kv-name="characteristics_ru"')

    def test_bound_characteristics_render_and_save(self):
        from apps.catalog.forms import ProductAdminForm

        form = ProductAdminForm({
            "category": str(self.category.pk),
            "sku": "ADM-NEW",
            "name": "Новий товар",
            "slug": "novyi-tovar-admin",
            "base_price": "12.50",
            "characteristics_key": ["тип"],
            "characteristics_value": ["овочеве"],
            "characteristics_ru_key": ["вид"],
            "characteristics_ru_value": ["2"],
        })
        self.assertIn("овочеве", str(form["characteristics"]))
        self.assertIn("вид", str(form["characteristics_ru"]))
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        product.refresh_from_db()
        self.assertEqual(product.characteristics, {"тип": "овочеве"})
        self.assertEqual(product.characteristics_ru, {"вид": "2"})

    def test_add_post_with_characteristics_does_not_500(self):
        response = self.client.post(
            "/admin/catalog/product/add/",
            {
                "category": self.category.pk,
                "sku": "ADM-POST",
                "name": "Товар POST",
                "slug": "tovar-post",
                "base_price": "9.00",
                "is_active": "on",
                "characteristics_key": ["тип"],
                "characteristics_value": ["1"],
                "characteristics_ru_key": ["вид"],
                "characteristics_ru_value": ["2"],
                "variants-TOTAL_FORMS": "1",
                "variants-INITIAL_FORMS": "0",
                "variants-MIN_NUM_FORMS": "0",
                "variants-MAX_NUM_FORMS": "1000",
                "images-TOTAL_FORMS": "1",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "1000",
                "_save": "Save",
            },
        )
        self.assertLess(response.status_code, 500)
