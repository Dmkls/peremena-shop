from django import forms
from django.core.validators import RegexValidator

from .models import Order


class CheckoutForm(forms.ModelForm):
    phone = forms.CharField(
        label="Телефон", max_length=30,
        validators=[RegexValidator(r"^\+?[\d\s()\-]{10,20}$", "Введите телефон, например +7 900 123-45-67.")],
    )

    class Meta:
        model = Order
        fields = ("full_name", "phone", "address", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=999)
