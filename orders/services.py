"""Бизнес-логика заказов: вынесена из views, чтобы её было удобно тестировать."""

from django.db import transaction
from django.db.models import Sum

from catalog.models import Product

from .models import CartItem, Order, OrderItem


class CheckoutError(Exception):
    pass


def cart_count(user):
    """Сколько штук товаров лежит в корзине (для значка в шапке)."""
    return CartItem.objects.filter(user=user).aggregate(n=Sum("quantity"))["n"] or 0


def add_to_cart(user, product, quantity=1):
    item, created = CartItem.objects.get_or_create(user=user, product=product,
                                                   defaults={"quantity": 0})
    item.quantity = min(item.quantity + quantity, product.stock)
    if item.quantity < 1:
        item.delete()
        raise CheckoutError("Товара нет в наличии.")
    item.save()
    return item


@transaction.atomic
def place_order(user, contact_data):
    """Создаёт заказ из корзины пользователя, списывает остатки и очищает корзину.

    Всё в одной транзакции: либо заказ создан полностью, либо ничего не изменилось.
    """
    items = list(CartItem.objects.filter(user=user).select_related("product"))
    if not items:
        raise CheckoutError("Корзина пуста.")

    # Блокируем строки товаров, чтобы два одновременных заказа не продали один и тот же остаток.
    products = Product.objects.select_for_update().in_bulk([i.product_id for i in items])

    for item in items:
        product = products[item.product_id]
        if not product.is_active:
            raise CheckoutError(f"Товар «{product.name}» больше не продаётся.")
        if product.stock < item.quantity:
            raise CheckoutError(f"Товара «{product.name}» осталось только {product.stock} шт.")

    order = Order.objects.create(user=user, **contact_data)
    for item in items:
        product = products[item.product_id]
        OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                 price=product.price, quantity=item.quantity)
        product.stock -= item.quantity
        product.save(update_fields=["stock"])

    CartItem.objects.filter(user=user).delete()
    return order


@transaction.atomic
def change_status(order, new_status):
    """Меняет статус заказа. При отмене возвращает товары на склад, при «возврате из отмены» — снова списывает."""
    old_status = order.status
    if old_status == new_status:
        return order

    cancelled = Order.Status.CANCELLED
    if cancelled in (old_status, new_status):
        sign = 1 if new_status == cancelled else -1
        for item in order.items.select_related("product"):
            if item.product is None:
                continue
            product = Product.objects.select_for_update().get(pk=item.product_id)
            if sign < 0 and product.stock < item.quantity:
                raise CheckoutError(f"Недостаточно «{product.name}» на складе, чтобы восстановить заказ.")
            product.stock += sign * item.quantity
            product.save(update_fields=["stock"])

    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    return order
