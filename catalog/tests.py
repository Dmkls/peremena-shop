from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.notebooks = Category.objects.create(name="Тетради и блокноты")
        cls.bags = Category.objects.create(name="Рюкзаки")
        cls.cheap = Product.objects.create(category=cls.notebooks, name="Тетрадь в клетку", price=Decimal("89"), stock=5)
        cls.pricey = Product.objects.create(category=cls.bags, name="Рюкзак", price=Decimal("3490"), stock=0)
        cls.hidden = Product.objects.create(category=cls.bags, name="Скрытый рюкзак", price=Decimal("1"), is_active=False)

    def names(self, **params):
        response = self.client.get(reverse("catalog:product_list"), params)
        return [p.name for p in response.context["page"].object_list]

    def test_slug_is_transliterated(self):
        self.assertEqual(self.notebooks.slug, "tetradi-i-bloknoty")

    def test_search_is_case_insensitive_for_cyrillic(self):
        self.assertEqual(self.names(q="ТЕТРАДЬ"), ["Тетрадь в клетку"])

    def test_filters_and_sort(self):
        self.assertEqual(self.names(category="ryukzaki"), ["Рюкзак"])
        self.assertEqual(self.names(price_min=100), ["Рюкзак"])
        self.assertEqual(self.names(in_stock="on"), ["Тетрадь в клетку"])
        self.assertEqual(self.names(sort="-price"), ["Рюкзак", "Тетрадь в клетку"])

    def test_hidden_product_not_shown_to_guest(self):
        self.assertNotIn("Скрытый рюкзак", self.names())
        response = self.client.get(self.hidden.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_pages_render(self):
        for url in (reverse("catalog:home"), reverse("catalog:product_list"), self.cheap.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200, url)
