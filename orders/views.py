from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product

from .forms import CartQuantityForm, CheckoutForm
from .models import CartItem, Order
from .services import CheckoutError, add_to_cart, cart_count, place_order


def _cart_items(user):
    return CartItem.objects.filter(user=user).select_related("product", "product__category")


@login_required
def cart_detail(request):
    items = _cart_items(request.user)
    total = sum((i.total for i in items), Decimal("0"))
    return render(request, "orders/cart.html", {"items": items, "total": total})


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product.objects.available(), pk=product_id)
    form = CartQuantityForm(request.POST)
    quantity = form.cleaned_data["quantity"] if form.is_valid() else 1
    try:
        add_to_cart(request.user, product, max(quantity, 1))
        ok, text = True, f"«{product.name}» в корзине."
    except CheckoutError as e:
        ok, text = False, str(e)

    # Запрос из main.js: отвечаем JSON, страница не перезагружается.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": ok, "message": text, "cart_count": cart_count(request.user)},
                            status=200 if ok else 400)

    (messages.success if ok else messages.error)(request, text)
    # Возвращаем туда, откуда пришли, но только на свой же сайт (защита от open redirect).
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
        return redirect(next_url)
    return redirect("orders:cart")


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    form = CartQuantityForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        if quantity == 0:
            item.delete()
        else:
            item.quantity = min(quantity, item.product.stock)
            item.save(update_fields=["quantity"])
            if quantity > item.product.stock:
                messages.warning(request, f"На складе только {item.product.stock} шт. «{item.product.name}».")
    return redirect("orders:cart")


@login_required
@require_POST
def cart_remove(request, item_id):
    get_object_or_404(CartItem, pk=item_id, user=request.user).delete()
    return redirect("orders:cart")


@login_required
def checkout(request):
    items = _cart_items(request.user)
    if not items:
        messages.info(request, "Корзина пуста — добавьте товары из каталога.")
        return redirect("catalog:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(request.user, form.cleaned_data)
            except CheckoutError as e:
                messages.error(request, str(e))
                return redirect("orders:cart")
            messages.success(request, f"Заказ №{order.pk} оформлен! Мы скоро свяжемся с вами.")
            return redirect(order)
    else:
        user = request.user
        form = CheckoutForm(initial={"full_name": user.get_full_name() or user.username})

    total = sum((i.total for i in items), Decimal("0"))
    return render(request, "orders/checkout.html", {"form": form, "items": items, "total": total})


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    # Фильтр по user: чужой заказ даёт 404, а не 403, — не раскрываем, что он существует.
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
