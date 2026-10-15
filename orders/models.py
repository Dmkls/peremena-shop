from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from catalog.models import Product


class CartItem(models.Model):
    """Позиция корзины. Корзина есть только у авторизованного покупателя."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="покупатель",
                             on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("количество", default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField("добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "позиция корзины"
        verbose_name_plural = "позиции корзины"
        ordering = ["added_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_cart_product"),
        ]

    def __str__(self):
        return f"{self.product} × {self.quantity}"

    @property
    def total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        ASSEMBLING = "assembling", "Собирается на складе"
        SHIPPED = "shipped", "Передан службе доставки"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="покупатель",
                             on_delete=models.PROTECT, related_name="orders")
    status = models.CharField("статус", max_length=20, choices=Status.choices, default=Status.NEW)
    full_name = models.CharField("ФИО получателя", max_length=150)
    phone = models.CharField("телефон", max_length=30)
    address = models.CharField("адрес доставки", max_length=255)
    comment = models.TextField("комментарий", blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ №{self.pk}"

    def get_absolute_url(self):
        return reverse("orders:order_detail", args=[self.pk])

    @property
    def total(self):
        return sum((item.total for item in self.items.all()), Decimal("0"))


class OrderItem(models.Model):
    """Позиция заказа. Название и цена копируются в момент покупки,
    чтобы заказ не менялся, если товар потом отредактируют или удалят."""

    order = models.ForeignKey(Order, verbose_name="заказ", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="order_items")
    product_name = models.CharField("название товара", max_length=200)
    price = models.DecimalField("цена за шт., ₽", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("количество", validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def total(self):
        return self.price * self.quantity
