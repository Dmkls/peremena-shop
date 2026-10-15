from .services import cart_count


def cart(request):
    """Количество товаров в корзине для значка в шапке."""
    if not request.user.is_authenticated:
        return {"cart_count": 0}
    return {"cart_count": cart_count(request.user)}
