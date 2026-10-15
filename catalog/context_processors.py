from .models import Category


def categories(request):
    """Список категорий для меню на всех страницах (запрос ленивый)."""
    return {"nav_categories": Category.objects.all()}
