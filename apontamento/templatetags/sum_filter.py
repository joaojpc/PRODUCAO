from django import template

register = template.Library()

@register.filter
def sum_field(values, field_name):
    return sum(float(value.get(field_name, 0)) for value in values)
@register.filter
def format_number(value, decimal_places=2):
    return '{:,.{}f}'.format(value, decimal_places).replace('.', '#').replace(',', '.').replace('#', ',')
