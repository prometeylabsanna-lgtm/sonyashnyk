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
