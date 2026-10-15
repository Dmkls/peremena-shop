from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Неверный логин или пароль.",
    }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="Имя", max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Короткий чек-лист вместо стандартного списка; main.js подсвечивает выполненные правила.
        # Остальные валидаторы (похожесть на логин, слишком простой пароль) по-прежнему проверяются на сервере.
        self.fields["password1"].help_text = (
            '<ul class="pw-rules">'
            '<li data-rule="length">Минимум 8 символов</li>'
            '<li data-rule="not-numeric">Не только из цифр</li>'
            "</ul>"
        )
        self.fields["password1"].widget.attrs["data-password-rules"] = ""

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email
