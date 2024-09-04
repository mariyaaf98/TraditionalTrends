
from cart_management.models import Cart, CartItem
from wishlist.models import WishlistItem

def cart_context_processor(request):
    cart = None
    cart_items = []
    wishlist_item_count = 0
    total_price = 0
    cart_item_count = 0

    if request.user.is_authenticated:
        # Cart details
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.variant.product.offer_price * item.quantity for item in cart_items)
        cart_item_count = cart_items.count() 

        # Wishlist details
        wishlist_items = WishlistItem.objects.filter(user=request.user)
        wishlist_item_count = wishlist_items.count()

    return {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'wishlist_item_count': wishlist_item_count,
        'cart_item_count': cart_item_count,
    }

