from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .utils import make_slug


class Category(models.Model):
    name = models.CharField("название", max_length=100, unique=True)
    slug = models.SlugField("адрес (slug)", max_length=120, unique=True, blank=True,
                            help_text="Латиница, цифры и дефисы. Если оставить пустым — заполнится автоматически.")
    description = models.TextField("описание", blank=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_slug(self.name, Category, instance=self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('catalog:product_list')}?category={self.slug}"


class ProductQuerySet(models.QuerySet):
    def available(self):
        """Товары, которые видит покупатель."""
        return self.filter(is_active=True)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="категория",
        on_delete=models.PROTECT,  # нельзя удалить категорию, пока в ней есть товары
        related_name="products",
    )
    name = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    price = models.DecimalField("цена, ₽", max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField("остаток на складе", default=0)
    image = models.ImageField("изображение", upload_to="products/%Y/%m/", blank=True)
    is_active = models.BooleanField("показывать в каталоге", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)
    # SQLite не умеет регистронезависимо сравнивать кириллицу,
    # поэтому для поиска храним название и описание в нижнем регистре.
    search_text = models.TextField(editable=False, default="")

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "category"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_text = f"{self.name} {self.description}".lower()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.pk])

    @property
    def in_stock(self):
        return self.stock > 0
