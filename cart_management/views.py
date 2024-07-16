from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from cart_management.models import Cart, CartItem
from product_management.models import Product_Variant, Products
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
@require_POST
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id', None)
    quantity = int(request.POST.get('quantity', 1))

    product = get_object_or_404(Products, id=product_id)

    if variant_id:
        variant = get_object_or_404(Product_Variant, id=variant_id, product_id=product_id)
        if not variant.variant_status or variant.is_deleted:
            return JsonResponse({'error': 'Variant is not available'}, status=400)
        if quantity > variant.variant_stock:
            return JsonResponse({'error': 'Quantity exceeds available stock'}, status=400)
    else:
        variant = None

    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)

    if variant:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
    else:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        new_quantity = cart_item.quantity + quantity
        if variant and new_quantity > variant.variant_stock:
            return JsonResponse({'error': 'Quantity exceeds available stock'}, status=400)
        cart_item.quantity = new_quantity
    else:
        cart_item.quantity = quantity

    cart_item.save()

    response_data = {
        'message': 'Product added to cart!',
        'product_name': product.product_name,
        'quantity': cart_item.quantity,
        'price': str(product.price),
        'offer_price': str(product.offer_price)
    }

    if variant:
        response_data['variant_color'] = variant.colour_name

    return JsonResponse(response_data, status=200)

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(cart__user=request.user).select_related('variant__product')

    cart_total = sum(item.quantity * (item.variant.product.offer_price if item.variant else item.product.offer_price) for item in cart_items)

    context = {
        'cart_items': [
            {
                'id': item.id,
                'variant': item.variant,
                'product': item.variant.product if item.variant else item.product,
                'quantity': item.quantity,
                'available_stock': item.variant.variant_stock if item.variant else item.product.stock,
            }
            for item in cart_items
        ],
        'cart_total': cart_total,
    }
    return render(request, 'user_side/shop-cart.html', context)

@login_required
@require_POST
def update_cart_item(request, item_id):
    quantity = int(request.POST.get('quantity', 1))

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__is_active=True)
    variant = cart_item.variant

    if variant and quantity > variant.variant_stock:
        return JsonResponse({'error': 'Quantity exceeds available stock'}, status=400)

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()

        item_total_price = cart_item.quantity * cart_item.variant.product.offer_price
        cart_items = cart_item.cart.items.all()
        cart_total_price = sum(item.quantity * item.variant.product.offer_price for item in cart_items)

        response = {
            'success': True,
            'item_total_price': item_total_price,
            'cart_total_price': cart_total_price
        }
    else:
        cart_item.delete()
        cart_items = CartItem.objects.filter(cart=cart_item.cart)
        cart_total_price = sum(item.quantity * item.variant.product.offer_price for item in cart_items)
        response = {
            'success': True,
            'item_total_price': 0,
            'cart_total_price': cart_total_price
        }

    return JsonResponse(response)

@login_required
@require_POST
def delete_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    # Calculate the new cart total after item removal
    cart_items = CartItem.objects.filter(cart__user=request.user)
    cart_total = sum(item.quantity * item.variant.product.offer_price for item in cart_items)

    return JsonResponse({'success': True, 'cart_total': cart_total})

@login_required
def clear_cart(request):
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    if cart:
        cart.items.all().delete()
    return redirect('cart_management:cart')

@login_required
@require_POST
def quantity_update(request, id):
    quantity = request.POST.get("qty")
    print(quantity)
    data = Cart.objects.get(id=id)
    data.quantity = quantity
    data.save()

    return redirect("cart:product-cart")



    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'User is not logged in'}, status=403)
   
