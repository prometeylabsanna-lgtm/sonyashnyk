from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product


class RecentActionsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser("recent_admin", "r@a.com", "pass")
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Category.objects.create(name="Тест", slug="test-recent-act")

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
    def test_recent_actions_page_shows_all_models(self):
        product = Product.objects.create(
            category=self.cat,
            sku="REC-001",
            name="Товар для логу",
            base_price="10.00",
            is_active=True,
        )
        LogEntry.objects.log_action(
            user_id=self.user.pk,
            content_type_id=ContentType.objects.get_for_model(Product).pk,
            object_id=str(product.pk),
            object_repr=str(product),
            action_flag=ADDITION,
            change_message="Додано через тест",
        )
        LogEntry.objects.log_action(
            user_id=self.user.pk,
            content_type_id=ContentType.objects.get_for_model(Category).pk,
            object_id=str(self.cat.pk),
            object_repr=str(self.cat),
            action_flag=CHANGE,
            change_message="Змінено категорію",
        )
        url = reverse("admin:catalog_recent_product_actions")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("Недавні дії", body)
        self.assertIn("Товар для логу", body)
        self.assertIn("Додано", body)
        self.assertIn("Змінено", body)
        self.assertIn("Тест", body)
        self.assertIn("recent_admin", body)

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
    def test_dashboard_has_no_recent_actions_widget(self):
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn("recent-actions-module", body)
        self.assertNotIn("id=\"content-related\"", body)
