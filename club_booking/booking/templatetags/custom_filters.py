from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    """Получает значение словаря по ключу"""
    return d.get(key, '')