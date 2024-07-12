from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def cart_total(cart_items):
    total = sum(item.quantity * item.variant.product.offer_price for item in cart_items)
    return total