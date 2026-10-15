from django import forms

from catalog.models import Category, Product
from orders.models import Order

MAX_IMAGE_MB = 5


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "description", "price", "stock", "image", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and image.size > MAX_IMAGE_MB * 1024 * 1024:
            raise forms.ValidationError(f"Файл больше {MAX_IMAGE_MB} МБ.")
        return image


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(label="Статус", choices=Order.Status.choices)
