from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation

from apps.catalog.category_tree import pack_measure_kind, pack_measure_label
from apps.catalog.filters import filter_products
from apps.catalog.models import Category, Product, ProductVariant
from apps.catalog.product_merge import MergeError, merge_products, strip_pack_from_name


def _category(name, slug, parent=None):
    return Category.objects.create(name=name, slug=slug, parent=parent)


class PackMeasureLabelTests(TestCase):
    def test_soils_are_volume(self):
        root = _category("Грунти", "grunti-ta-vse-dlia-posadki")
        leaf = _category("Субстрати", "substraty", root)
        self.assertEqual(pack_measure_kind(leaf, "10 л"), "volume")
        self.assertEqual(pack_measure_kind(leaf, "50 л"), "volume")

    def test_weight_seeds_are_weight(self):
        root = _category("Насіння", "nasinnia")
        leaf = _category("Вагове насіння", "vagove-nasinnia", root)
        self.assertEqual(pack_measure_kind(leaf, "0,5 кг"), "weight")

    def test_packed_seeds_are_pieces(self):
        root = _category("Насіння", "nasinnia")
        mid = _category("Насіння овочів", "nasinnia-ovochiv", root)
        leaf = _category("Томати", "tomaty", mid)
        self.assertEqual(pack_measure_kind(leaf, "10 шт"), "pieces")
        lawn = _category("Газонні трави", "gazonni-travi", root)
        self.assertEqual(pack_measure_kind(lawn, "1 упак."), "pieces")

    def test_liquid_and_dry_fertilizers(self):
        root = _category("Добрива", "dobriva-ta-stimuliatori-rostu")
        leaf = _category("Мінеральні", "mineralni-dobriva", root)
        self.assertEqual(pack_measure_kind(leaf, "1 л"), "volume")
        self.assertEqual(pack_measure_kind(leaf, "100 мл"), "volume")
        self.assertEqual(pack_measure_kind(leaf, "500 г"), "weight")
        self.assertEqual(pack_measure_kind(leaf, "5 кг"), "weight")

    def test_liquid_and_dry_chemistry(self):
        root = _category("ЗЗР", "zasobi-zakhistu-roslin")
        leaf = _category("Фунгіциди", "funhitsidi", root)
        self.assertEqual(pack_measure_kind(leaf, "6 мл"), "volume")
        self.assertEqual(pack_measure_kind(leaf, "10 кг"), "weight")

    def test_labels_uk_and_ru(self):
        root = _category("Ґрунти", "grunti-ta-vse-dlia-posadki")
        with translation.override("uk"):
            self.assertEqual(pack_measure_label(root, "10 л"), "Обʼєм")
        with translation.override("ru"):
            self.assertEqual(pack_measure_label(root, "10 л"), "Объём")

    def test_product_property(self):
        root = _category("Насіння 2", "nasinnia-2")
        leaf = _category("Вагове 2", "vagove-nasinnia-x", root)
        # slug must be the weight slug
        leaf.slug = "vagove-nasinnia"
        leaf.save(update_fields=["slug"])
        product = Product.objects.create(
            category=leaf,
            sku="SKU-PACK-1",
            name="Конюшина",
            pack_volume="1 кг",
            base_price="100.00",
        )
        with translation.override("uk"):
            self.assertEqual(product.pack_measure_label, "Вага")


def _product(category, sku, name, pack_volume, price="100.00"):
    return Product.objects.create(
        category=category,
        sku=sku,
        name=name,
        pack_volume=pack_volume,
        base_price=price,
    )


class PackSwitchTests(TestCase):
    def setUp(self):
        self.category = _category("ЗЗР", "zzr-pack")
        self.product = _product(self.category, "SKU-HUR-100", "Ураган 100 мл", "100 мл")
        ProductVariant.objects.create(
            product=self.product, label="100 мл", sku_variant="SKU-HUR-100",
            price="80.00", stock_qty=5, is_default=True, order=0,
        )
        ProductVariant.objects.create(
            product=self.product, label="300 мл", sku_variant="SKU-HUR-300",
            price="150.00", stock_qty=2, order=1,
        )
        ProductVariant.objects.create(
            product=self.product, label="1 л", sku_variant="SKU-HUR-1L",
            price="320.00", stock_qty=0, order=2,
        )

    def test_has_pack_choices(self):
        self.assertTrue(self.product.has_pack_choices)
        self.assertEqual(len(self.product.pack_variants), 3)
        self.assertEqual(self.product.default_variant.label, "100 мл")

    def test_card_renders_pack_buttons(self):
        html = render_to_string("includes/product_card.html", {"product": self.product})
        self.assertIn("data-pack-option", html)
        self.assertIn("100 мл", html)
        self.assertIn("300 мл", html)
        self.assertIn("1 л", html)
        self.assertIn('data-variant-id="%s"' % self.product.default_variant.id, html)
        self.assertIn("Обʼєм", html)
        self.assertNotIn("Фасування", html)
        self.assertNotIn("Фасовка", html)
        self.assertNotRegex(html, r">\s*[SML]\s*<")
        self.assertNotIn("Потужність", html)
        self.assertNotIn("Мощность", html)

    def test_volume_filter_matches_variant_label(self):
        from apps.catalog.filters import annotate_card_price

        request = RequestFactory().get("/katalog/", {"volume": "1 л"})
        qs = filter_products(request, annotate_card_price(Product.objects.filter(is_active=True)))
        self.assertIn(self.product, list(qs))

    def test_price_filter_uses_variant_price_not_base(self):
        from apps.catalog.filters import annotate_card_price

        # base_price у діапазоні, ціна варіанта — ні
        self.product.base_price = Decimal("150.00")
        self.product.save(update_fields=["base_price"])
        for v in self.product.variants.all():
            v.price = Decimal("500.00")
            v.save(update_fields=["price"])

        request = RequestFactory().get("/katalog/", {"price_min": "100", "price_max": "200"})
        qs = filter_products(request, annotate_card_price(Product.objects.filter(is_active=True)))
        self.assertNotIn(self.product, list(qs))

        request2 = RequestFactory().get("/katalog/", {"price_min": "400", "price_max": "600"})
        qs2 = filter_products(request2, annotate_card_price(Product.objects.filter(is_active=True)))
        self.assertIn(self.product, list(qs2))

    def test_invalid_price_param_ignored(self):
        from apps.catalog.filters import annotate_card_price

        request = RequestFactory().get("/katalog/", {"price_min": "abc"})
        qs = filter_products(request, annotate_card_price(Product.objects.filter(is_active=True)))
        self.assertIn(self.product, list(qs))

    def test_weight_and_pieces_are_separate_filters(self):
        from apps.catalog.filter_models import CatalogFilter

        slugs = set(CatalogFilter.objects.values_list("slug", flat=True))
        self.assertIn("volume", slugs)
        self.assertIn("weight", slugs)
        self.assertIn("pieces", slugs)
        self.assertNotIn("power", slugs)
        volume = CatalogFilter.objects.get(slug="volume")
        self.assertEqual(volume.name, "Обʼєм")
        self.assertEqual(CatalogFilter.objects.get(slug="weight").name, "Вага")
        self.assertEqual(CatalogFilter.objects.get(slug="pieces").name, "Кількість шт")

    def test_offer_variant_prefers_in_stock(self):
        default = self.product.default_variant
        default.stock_qty = 0
        default.save(update_fields=["stock_qty"])
        offer = self.product.offer_variant
        self.assertIsNotNone(offer)
        self.assertGreater(offer.stock_qty, 0)
        self.assertNotEqual(offer.id, default.id)

    def test_old_price_hidden_when_not_higher(self):
        variant = self.product.offer_variant
        variant.old_price = variant.price
        variant.save(update_fields=["old_price"])
        self.assertIsNone(self.product.display_old_price)


class ProductMergeTests(TestCase):
    def setUp(self):
        self.category = _category("Гербіциди", "gerbitsydi")
        self.p100 = _product(self.category, "H-100", "Ураган 100 мл", "100 мл", "80.00")
        self.p300 = _product(self.category, "H-300", "Ураган 300 мл", "300 мл", "150.00")
        self.p1l = _product(self.category, "H-1L", "Ураган 1 л", "1 л", "320.00")
        ProductVariant.objects.create(
            product=self.p100, label="100 мл", sku_variant="H-100",
            price="80.00", stock_qty=4, is_default=True,
        )
        ProductVariant.objects.create(
            product=self.p300, label="300 мл", sku_variant="H-300",
            price="150.00", stock_qty=3, is_default=True,
        )
        ProductVariant.objects.create(
            product=self.p1l, label="1 л", sku_variant="H-1L",
            price="320.00", stock_qty=1, is_default=True,
        )

    def test_strip_pack_from_name(self):
        self.assertEqual(strip_pack_from_name("Ураган 100 мл"), "Ураган")
        self.assertEqual(strip_pack_from_name("Ураган Форте 1 л"), "Ураган Форте")

    def test_merge_requires_two(self):
        with self.assertRaises(MergeError):
            merge_products(Product.objects.filter(pk=self.p100.pk))

    def test_merge_three_skus_into_one(self):
        parent, hidden = merge_products(
            Product.objects.filter(pk__in=[self.p100.pk, self.p300.pk, self.p1l.pk])
        )
        parent.refresh_from_db()
        labels = list(parent.variants.order_by("order").values_list("label", flat=True))
        self.assertEqual(parent.name, "Ураган")
        self.assertCountEqual(labels, ["100 мл", "300 мл", "1 л"])
        self.assertTrue(parent.has_pack_choices)
        self.assertEqual(len(hidden), 2)
        for child in hidden:
            child.refresh_from_db()
            self.assertFalse(child.is_active)
            self.assertEqual(child.variants.count(), 0)


class SizePackRewriteTests(TestCase):
    def test_seed_sml_become_piece_counts(self):
        from apps.catalog.category_tree import rewrite_size_variant_labels

        root = _category("Насіння", "nasinnia")
        leaf = _category("Томати", "tomaty-sml", root)
        product = _product(leaf, "SKU-SML", "Томат", "")
        for order, size in enumerate(("S", "M", "L")):
            ProductVariant.objects.create(
                product=product, label=size, price="40.00", stock_qty=3,
                is_default=(order == 0), order=order,
            )
        self.assertTrue(rewrite_size_variant_labels(product))
        product.refresh_from_db()
        labels = list(product.variants.order_by("order").values_list("label", flat=True))
        self.assertEqual(labels, ["5 шт", "10 шт", "20 шт"])
        self.assertEqual(product.pack_volume, "5 шт")
        html = render_to_string("includes/product_card.html", {"product": product})
        self.assertIn("Кількість шт", html)
        self.assertNotIn("Фасування", html)
        self.assertNotIn(">S<", html)
        self.assertNotIn("Потужність", html)


class SearchHardenTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-search")
        self.product = Product.objects.create(
            category=cat, sku="SKU-SRCH", name="привіт насіння", base_price=Decimal("10.00"),
        )
        ProductVariant.objects.create(
            product=self.product, label="1", price=Decimal("10.00"), stock_qty=3, is_default=True,
        )
        Product.objects.create(
            category=cat, sku="SKU-OTHER", name="Інший товар", base_price=Decimal("15.00"),
        )

    def test_special_queries_do_not_500(self):
        for q in ("' OR 1=1", "<script>alert(1)</script>", "🔥", "%", "NULL", "&"):
            resp = self.client.get(reverse("search"), {"q": q})
            self.assertEqual(resp.status_code, 200, msg=q)

    def test_percent_does_not_match_all(self):
        resp = self.client.get(reverse("search"), {"q": "%"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["total_count"], 0)

    def test_layout_remap_finds_cyrillic(self):
        # На EN-розкладці «ghbdsn» = «привіт» (і на клавіші s)
        resp = self.client.get(reverse("search"), {"q": "ghbdsn"})
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.context["total_count"], 1)
        self.assertIn(self.product, list(resp.context["products"].object_list))


class PaginationClampTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кат", slug="cat-page")
        for i in range(13):
            p = Product.objects.create(
                category=cat, sku=f"SKU-P{i}", name=f"Товар {i}",
                base_price=Decimal("10.00"), is_active=True,
            )
            ProductVariant.objects.create(
                product=p, label="1", price=Decimal("10.00"), stock_qty=1, is_default=True,
            )

    def test_high_page_clamps_to_last(self):
        resp = self.client.get(reverse("catalog:index"), {"page": 99})
        self.assertEqual(resp.status_code, 200)
        page = resp.context["products"]
        self.assertTrue(page.object_list)
        self.assertEqual(page.number, page.paginator.num_pages)
        self.assertTrue(resp.context["page_clamped"])

