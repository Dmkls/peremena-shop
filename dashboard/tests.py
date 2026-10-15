from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product

User = get_user_model()


class DashboardAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin", password="pass12345!", is_staff=True)
        cls.buyer = User.objects.create_user("buyer", password="pass12345!")
        cls.category = Category.objects.create(name="Канцелярия")
        cls.product = Product.objects.create(category=cls.category, name="Ручка", price=Decimal("45"), stock=5)

    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_buyer_gets_403_everywhere(self):
        self.client.force_login(self.buyer)
        urls = [
            reverse("dashboard:index"),
            reverse("dashboard:product_list"),
            reverse("dashboard:product_create"),
            reverse("dashboard:product_delete", args=[self.product.pk]),
            reverse("dashboard:order_list"),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        # и POST-действие тоже не проходит
        self.client.post(reverse("dashboard:product_delete", args=[self.product.pk]))
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_admin_can_create_edit_delete_product(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:product_create"), {
            "name": "Тетрадь", "category": self.category.pk, "description": "",
            "price": "89", "stock": "10", "is_active": "on",
        })
        product = Product.objects.get(name="Тетрадь")

        self.client.post(reverse("dashboard:product_edit", args=[product.pk]), {
            "name": "Тетрадь 48 л.", "category": self.category.pk, "description": "",
            "price": "99", "stock": "10", "is_active": "on",
        })
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal("99"))

        self.client.post(reverse("dashboard:product_delete", args=[product.pk]))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_category_with_products_is_not_deleted(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:category_delete", args=[self.category.pk]))
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
