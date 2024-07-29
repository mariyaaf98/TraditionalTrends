
from cart_management.models import Cart, CartItem

def cart_context_processor(request):
    cart = None
    cart_items = []
    total_price = 0


    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.variant.product.offer_price * item.quantity for item in cart_items)

    return {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
