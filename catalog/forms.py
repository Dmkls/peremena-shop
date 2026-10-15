from django import forms

from .models import Category


class CatalogFilterForm(forms.Form):
    """Параметры поиска/фильтрации/сортировки каталога (GET-запрос)."""

    SORT_CHOICES = [
        ("new", "Сначала новые"),
        ("price", "Сначала дешевле"),
        ("-price", "Сначала дороже"),
        ("name", "По названию"),
    ]
    SORT_FIELDS = {"new": "-created_at", "price": "price", "-price": "-price", "name": "name"}

    q = forms.CharField(label="Поиск", required=False, max_length=100)
    category = forms.ModelChoiceField(
        label="Категория", queryset=Category.objects.all(), to_field_name="slug",
        required=False, empty_label="Все категории",
    )
    price_min = forms.DecimalField(label="Цена от", required=False, min_value=0)
    price_max = forms.DecimalField(label="Цена до", required=False, min_value=0)
    in_stock = forms.BooleanField(label="Только в наличии", required=False)
    sort = forms.ChoiceField(label="Сортировка", choices=SORT_CHOICES, required=False)

    def filter(self, qs):
        if not self.is_valid():
            return qs
        data = self.cleaned_data
        if data["q"]:
            qs = qs.filter(search_text__contains=data["q"].strip().lower())
        if data["category"]:
            qs = qs.filter(category=data["category"])
        if data["price_min"] is not None:
            qs = qs.filter(price__gte=data["price_min"])
        if data["price_max"] is not None:
            qs = qs.filter(price__lte=data["price_max"])
        if data["in_stock"]:
            qs = qs.filter(stock__gt=0)
        return qs.order_by(self.SORT_FIELDS.get(data["sort"] or "new"))
