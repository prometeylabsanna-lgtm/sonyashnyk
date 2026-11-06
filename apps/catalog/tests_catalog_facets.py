"""NULL у фасетах каталогу не валить /katalog/ і не стирає справжні значення."""

from decimal import Decimal

from django.test import Client, TestCase, override_settings

from apps.catalog.filter_models import CatalogFilter, CatalogFilterCategory, CatalogFilterValue
from apps.catalog.models import Category, Product, ProductVariant


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class NullFacetCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seeds = Category.objects.create(name="Насіння", slug="nasinnia", is_active=True)
        self.other = Category.objects.create(name="Інше", slug="inshe-facet", is_active=True)
        pieces = CatalogFilter.objects.get(slug="pieces")
        CatalogFilterCategory.objects.get_or_create(
            catalog_filter=pieces,
            category=self.seeds,
            defaults={"is_enabled": True},
        )
        CatalogFilterValue.objects.get_or_create(
            catalog_filter=pieces,
            value="10 шт",
            defaults={"is_active": True},
        )
        self._product(self.seeds, "SEED-1", "Насіння 1", label="5 шт")
        self._product(self.other, "VALID-1", "З фасуванням", label="10 шт")
        self._product(self.other, "NO-VAR", "Без варіанта", label=None)
        for index in range(12):
            self._product(self.other, f"FILL-{index}", f"Товар {index}", label="1 уп")

    def _product(self, category, sku, name, *, label):
        product = Product.objects.create(
            category=category,
            sku=sku,
            name=name,
            slug=sku.lower(),
            base_price=Decimal("15.00"),
            is_active=True,
        )
        if label is not None:
            ProductVariant.objects.create(
                product=product,
                label=label,
                price=Decimal("15.00"),
                stock_qty=2,
                is_default=True,
            )
        return product

    def test_index_and_paging_survive_null_facet_and_keep_real_values(self):
        index = self.client.get("/katalog/")
        page = self.client.get("/katalog/", {"page": "2"})
        category = self.client.get("/katalog/nasinnia/")
        self.assertEqual(index.status_code, 200)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(category.status_code, 200)
        self.assertIn("10 шт", index.content.decode())
        self.assertIn("5 шт", category.content.decode())
        self.assertNotIn(">None<", index.content.decode())
