from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product

from .models import CartItem, Order
from .services import CheckoutError, change_status, place_order

User = get_user_model()
CONTACTS = {"full_name": "Иван Иванов", "phone": "+7 900 123-45-67", "address": "Москва, ул. Ленина, 1"}


class OrdersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user("buyer", password="pass12345!")
        cls.other = User.objects.create_user("other", password="pass12345!")
        category = Category.objects.create(name="Тетради")
        cls.product = Product.objects.create(category=category, name="Тетрадь", price=Decimal("89"), stock=10)


class CartAccessTests(OrdersTestCase):
    def test_guest_is_redirected_to_login(self):
        for name in ("orders:cart", "orders:checkout", "orders:order_list"):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse(name)}",
                                 fetch_redirect_response=False)

    def test_add_to_cart_requires_post(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("orders:cart_add", args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_is_capped_by_stock(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("orders:cart_add", args=[self.product.pk]), {"quantity": 50})
        self.assertEqual(CartItem.objects.get(user=self.buyer).quantity, 10)

    def test_ajax_add_returns_cart_count(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:cart_add", args=[self.product.pk]), {"quantity": 2},
                                    headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.json()["cart_count"], 2)
        self.assertTrue(response.json()["ok"])

    def test_add_returns_to_next_page(self):
        self.client.force_login(self.buyer)
        url = self.product.get_absolute_url()
        response = self.client.post(reverse("orders:cart_add", args=[self.product.pk]), {"next": url})
        self.assertRedirects(response, url, fetch_redirect_response=False)

    def test_cannot_touch_someone_elses_cart_item(self):
        item = CartItem.objects.create(user=self.other, product=self.product, quantity=1)
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:cart_remove", args=[item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_external_next_is_ignored(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:cart_add", args=[self.product.pk]),
                                    {"next": "https://evil.example.com/"})
        self.assertRedirects(response, reverse("orders:cart"))


class CheckoutTests(OrdersTestCase):
    def test_place_order_moves_cart_to_order_and_decrements_stock(self):
        CartItem.objects.create(user=self.buyer, product=self.product, quantity=3)
        order = place_order(self.buyer, CONTACTS)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(order.total, Decimal("267"))
        self.assertEqual(order.items.get().product_name, "Тетрадь")
        self.assertFalse(CartItem.objects.filter(user=self.buyer).exists())

    def test_not_enough_stock_rolls_back(self):
        CartItem.objects.create(user=self.buyer, product=self.product, quantity=3)
        Product.objects.filter(pk=self.product.pk).update(stock=2)
        with self.assertRaises(CheckoutError):
            place_order(self.buyer, CONTACTS)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(user=self.buyer).exists())

    def test_checkout_view(self):
        CartItem.objects.create(user=self.buyer, product=self.product, quantity=1)
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:checkout"), CONTACTS)
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())

    def test_order_price_is_frozen(self):
        CartItem.objects.create(user=self.buyer, product=self.product, quantity=1)
        order = place_order(self.buyer, CONTACTS)
        Product.objects.filter(pk=self.product.pk).update(price=Decimal("500"))
        self.assertEqual(order.total, Decimal("89"))

    def test_cancel_returns_stock(self):
        CartItem.objects.create(user=self.buyer, product=self.product, quantity=4)
        order = place_order(self.buyer, CONTACTS)
        change_status(order, Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)


class OrderPrivacyTests(OrdersTestCase):
    def test_user_cannot_see_someone_elses_order(self):
        CartItem.objects.create(user=self.other, product=self.product, quantity=1)
        order = place_order(self.other, CONTACTS)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("orders:order_list")), f"№{order.pk}")
