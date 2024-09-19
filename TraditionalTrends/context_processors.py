
from cart_management.models import Cart, CartItem
from wishlist.models import WishlistItem
from category_management.models import Category
from django.db.models import Q

def cart_context_processor(request):
    cart = None
    cart_items = []
    wishlist_item_count = 0
    total_price = 0
    cart_item_count = 0
    category_id = None

    # categories list
    categories = Category.objects.filter(
        Q(is_deleted=False) &
        Q(is_available=True) &
        Q(products__is_active=True) &
        Q(products__is_deleted=False)
    ).distinct()

    category_id = request.GET.get('category')

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
        'categories': categories,
        'category_id': category_id,
    }

