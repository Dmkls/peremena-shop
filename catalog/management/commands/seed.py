from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product

# Фото товаров для демонстрационных данных
IMAGES_DIR = Path(__file__).resolve().parents[2] / "seed_images"

# название, описание, цена, остаток, файл картинки
CATALOG = {
    "Канцелярия": [
        ("Ручка гелевая, синяя", "Мягкое письмо, стержень 0,5 мм, прорезиненный упор.", "45", 120, "01.jpg"),
        ("Ручка перьевая", "Стальное перо, сменные картриджи с синими чернилами.", "349", 80, "02.jpg"),
        ("Карандаш чернографитный HB", "Заточенный, с ластиком. Корпус из липы.", "25", 200, "03.jpg"),
        ("Ножницы школьные", "Закруглённые концы, мягкие ручки, длина 13 см.", "129", 60, "04.jpg"),
        ("Линейка 30 см", "Пластиковая, с чёткой шкалой в сантиметрах.", "55", 90, "05.jpg"),
        ("Скрепки, 100 шт.", "Металлические, 28 мм, в пластиковой коробке.", "59", 4, "06.jpg"),
    ],
    "Тетради и блокноты": [
        ("Тетрадь 96 листов, клетка", "Плотная бумага 65 г/м², поля, твёрдая обложка.", "89", 150, "07.jpg"),
        ("Тетрадь 12 листов, линейка", "Классическая школьная тетрадь, 10 шт. в упаковке.", "199", 70, "08.jpg"),
        ("Блокнот A5 в точку", "120 листов, закладка-ляссе, резинка-фиксатор.", "249", 35, "09.jpg"),
        ("Папка для тетрадей А4", "Пластиковая, на резинке, вмещает до 20 тетрадей.", "149", 3, "10.jpg"),
    ],
    "Учебные пособия": [
        ("Python для начинающих", "Учебное пособие по программированию с задачами и разбором решений.", "790", 25, "11.jpg"),
        ("Алгебра. Сборник задач, 9 класс", "Более 1000 задач с ответами для подготовки к ОГЭ.", "450", 18, "12.jpg"),
        ("Английский язык. Грамматика", "Правила и упражнения от начального до среднего уровня.", "520", 0, "13.jpg"),
    ],
    "Рюкзаки": [
        ("Рюкзак школьный «Орбита»", "Ортопедическая спинка, 3 отделения, светоотражатели.", "3490", 12, "14.jpg"),
        ("Портфель для ноутбука", "Отделение для ноутбука 15,6\", плечевой ремень.", "2790", 8, "15.jpg"),
    ],
    "Товары для творчества": [
        ("Набор маркеров, 12 цветов", "Двусторонние, на спиртовой основе, не просвечивают.", "459", 40, "16.jpg"),
        ("Набор кистей для акварели", "6 синтетических кистей, круглые и плоские.", "380", 22, "17.jpg"),
        ("Акварель медовая, 24 цвета", "Яркие пигменты, кювета в пластиковом пенале.", "610", 15, "18.jpg"),
    ],
    "Компьютерные аксессуары": [
        ("Флешка 64 ГБ, USB 3.0", "Металлический корпус, скорость чтения до 120 МБ/с.", "690", 50, "19.jpg"),
        ("Мышь беспроводная", "Тихие клавиши, работает от одной батарейки AA до года.", "990", 14, "20.jpg"),
        ("Наушники с микрофоном", "Для онлайн-уроков: накладные, кабель 1,5 м.", "1290", 9, "21.jpg"),
    ],
}

DEMO_USERS = [
    # username, password, is_staff
    ("admin", "admin12345", True),
    ("buyer", "buyer12345", False),
]


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными категориями, товарами и (по флагу) пользователями."

    def add_arguments(self, parser):
        parser.add_argument("--with-users", action="store_true",
                            help="создать демо-аккаунты admin/admin12345 и buyer/buyer12345 (только для разработки!)")

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for category_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock, image in products:
                product, is_new = Product.objects.get_or_create(
                    name=name,
                    defaults={"category": category, "description": description,
                              "price": Decimal(price), "stock": stock},
                )
                created += is_new
                if not product.image:  # картинку, загруженную администратором, не трогаем
                    with open(IMAGES_DIR / image, "rb") as f:
                        product.image.save(image, File(f))
        self.stdout.write(self.style.SUCCESS(
            f"Категорий: {Category.objects.count()}, новых товаров: {created}."))

        if options["with_users"]:
            User = get_user_model()
            for username, password, is_staff in DEMO_USERS:
                if User.objects.filter(username=username).exists():
                    continue
                user = User(username=username, email=f"{username}@example.com",
                            is_staff=is_staff, is_superuser=is_staff)
                user.set_password(password)  # сохраняется только хеш
                user.save()
                self.stdout.write(f"Создан пользователь {username} / {password}")
