from django import template

register = template.Library()

@register.filter
def hyphenate(value):
    return value.replace(' ', '-').lower()
