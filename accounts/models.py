from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Пользователь магазина.

    Роли из ТЗ:
      * гость — неавторизованный посетитель (отдельной записи нет);
      * покупатель — обычный пользователь;
      * администратор — пользователь с is_staff=True.
    Пароль хранится только в виде хеша (PBKDF2 по умолчанию в Django).
    """
