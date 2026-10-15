from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .forms import CatalogFilterForm
from .models import Product


def home(request):
    products = Product.objects.available().select_related("category")[:8]
    return render(request, "catalog/home.html", {"products": products})


def product_list(request):
    form = CatalogFilterForm(request.GET or None)
    products = form.filter(Product.objects.available().select_related("category"))
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "catalog/product_list.html", {
        "form": form,
        "page": page,
        "current_category": form.cleaned_data.get("category") if form.is_bound and form.is_valid() else None,
    })


def product_detail(request, pk):
    qs = Product.objects.select_related("category")
    if not request.user.is_staff:  # скрытые товары видит только администратор
        qs = qs.available()
    product = get_object_or_404(qs, pk=pk)
    related = (Product.objects.available()
               .filter(category=product.category).exclude(pk=product.pk)[:4])
    return render(request, "catalog/product_detail.html", {"product": product, "related": related})


INFO_PAGES = {
    "delivery": ("Доставка", [
        "Доставляем по городу на следующий день после оформления заказа.",
        "Стоимость — 199 ₽, при заказе от 1 500 ₽ доставка бесплатная.",
        "Курьер позвонит за час до приезда.",
    ]),
    "payment": ("Оплата", [
        "Оплатить заказ можно при получении — картой или наличными.",
        "Курьер выдаст кассовый чек.",
    ]),
    "returns": ("Возврат", [
        "Вернуть товар надлежащего качества можно в течение 14 дней, если сохранены упаковка и чек.",
        "Деньги вернём в течение 10 дней после получения товара.",
    ]),
}


def info_page(request, slug):
    if slug not in INFO_PAGES:
        raise Http404
    title, paragraphs = INFO_PAGES[slug]
    return render(request, "catalog/info_page.html", {"title": title, "paragraphs": paragraphs})
