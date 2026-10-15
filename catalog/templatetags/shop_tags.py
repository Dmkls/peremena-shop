from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def rub(value):
    """3490.00 → «3 490 ₽», 45.50 → «45,50 ₽»."""
    if value in (None, ""):
        return ""
    return f"{floatformat(value, '-2g')} ₽"


@register.simple_tag(takes_context=True)
def url_with(context, **kwargs):
    """Текущий query string с заменёнными параметрами — для пагинации и сортировки."""
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return "?" + params.urlencode()
