from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Category, Product
from orders.models import Order
from orders.services import CheckoutError, change_status

from .decorators import staff_required
from .forms import CategoryForm, OrderStatusForm, ProductForm


@staff_required
def index(request):
    return render(request, "dashboard/index.html", {
        "products_count": Product.objects.count(),
        "categories_count": Category.objects.count(),
        "new_orders_count": Order.objects.filter(status=Order.Status.NEW).count(),
        "low_stock": Product.objects.filter(is_active=True, stock__lt=5).order_by("stock")[:10],
        "recent_orders": Order.objects.select_related("user")[:10],
    })


# ---------- товары ----------

@staff_required
def product_list(request):
    products = Product.objects.select_related("category").order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(search_text__contains=q.lower())
    page = Paginator(products, 25).get_page(request.GET.get("page"))
    return render(request, "dashboard/product_list.html", {"page": page, "q": q})


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"Товар «{product.name}» сохранён.")
        return redirect("dashboard:product_list")
    return render(request, "dashboard/product_form.html", {"form": form, "product": product})


@staff_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()  # в заказах останутся название и цена (OrderItem.product → NULL)
        messages.success(request, f"Товар «{product.name}» удалён.")
        return redirect("dashboard:product_list")
    return render(request, "dashboard/confirm_delete.html", {
        "object": product, "cancel_url": "dashboard:product_list",
    })


# ---------- категории ----------

@staff_required
def category_list(request):
    categories = Category.objects.annotate(products_count=Count("products"))
    return render(request, "dashboard/category_list.html", {"categories": categories})


@staff_required
def category_form(request, pk=None):
    category = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Категория «{category.name}» сохранена.")
        return redirect("dashboard:category_list")
    return render(request, "dashboard/category_form.html", {"form": form, "category": category})


@staff_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            category.delete()
        except ProtectedError:
            messages.error(request, "Нельзя удалить категорию, в которой есть товары. Сначала перенесите или удалите их.")
        else:
            messages.success(request, f"Категория «{category.name}» удалена.")
        return redirect("dashboard:category_list")
    return render(request, "dashboard/confirm_delete.html", {
        "object": category, "cancel_url": "dashboard:category_list",
    })


# ---------- заказы ----------

@staff_required
def order_list(request):
    orders = Order.objects.select_related("user").prefetch_related("items")
    status = request.GET.get("status")
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    page = Paginator(orders, 25).get_page(request.GET.get("page"))
    return render(request, "dashboard/order_list.html", {
        "page": page, "statuses": Order.Status.choices, "current_status": status,
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("user").prefetch_related("items"), pk=pk)
    form = OrderStatusForm(initial={"status": order.status})
    return render(request, "dashboard/order_detail.html", {"order": order, "form": form})


@staff_required
@require_POST
def order_set_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderStatusForm(request.POST)
    if form.is_valid():
        try:
            change_status(order, form.cleaned_data["status"])
            messages.success(request, f"Статус заказа №{order.pk}: {order.get_status_display()}.")
        except CheckoutError as e:
            messages.error(request, str(e))
    return redirect("dashboard:order_detail", pk=order.pk)
