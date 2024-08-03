from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from . models import Coupon
from cart_management . models import Cart
from .forms import CouponForm
import random
import string
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal

# def apply_coupon(request):
#     error_message = None
#     success_message = None

#     if request.method == 'POST':
#         code = request.POST.get('code')
#         try:
#             coupon = Coupon.objects.get(code=code, is_active=True)
#             if not coupon.is_valid():
#                 error_message = 'This coupon is expired, inactive, or has reached its usage limit'
#             else:
#                 # Apply coupon to the cart
#                 # Assuming you have a cart instance available
#                 cart = request.user.cart  # example of how to get the cart, adjust according to your implementation
#                 if coupon.minimum_purchase_amount and cart.get_total_price() < coupon.minimum_purchase_amount:
#                     error_message = 'This coupon requires a minimum purchase amount of ${}'.format(coupon.minimum_purchase_amount)
#                 else:
#                     if coupon.is_percentage:
#                         discount_amount = cart.get_total_price() * (coupon.discount / 100)
#                     else:
#                         discount_amount = coupon.discount

#                     cart.total_price -= discount_amount
#                     cart.coupon = coupon
#                     coupon.times_used += 1
#                     coupon.save()
#                     cart.save()
#                     success_message = 'Coupon applied successfully!'
#         except Coupon.DoesNotExist:
#             error_message = 'Invalid coupon code'

#     return render(request, 'admin_side/apply_coupon.html', {
#         'error_message': error_message,
#         'success_message': success_message
#     })

def generate_coupon_code(length=8):
    """Generate a random coupon code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            # Ensure the coupon code is unique
            while Coupon.objects.filter(code=coupon.code).exists():
                coupon.code = generate_coupon_code()
            coupon.save()
            messages.success(request, 'Coupon created successfully!')
            return redirect('cupon_management:coupon-list') 
    else:
        form = CouponForm()
    
    return render(request, 'admin_side/create_coupon.html', {'form': form})

def coupon_list(request):
    coupons = Coupon.objects.filter(is_active=True)  
    paginator = Paginator(coupons, 20)  # Show 20 coupons per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_side/coupon_list.html', {'page_obj': page_obj})


def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon updated successfully!')
            return redirect('cupon_management:coupon-list')
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'admin_side/edit_coupon.html', {'form': form, 'coupon': coupon})

def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.is_active = False  # Mark as inactive
        coupon.save()
        messages.success(request, 'Coupon delete successfully!')
        return redirect(request.META.get('HTTP_REFERER'))  # Redirect to the same page
    return redirect('cupon_management:coupon_list')


@require_POST
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code')
    
    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid or expired coupon code.'})

    if not coupon.is_valid():
        return JsonResponse({'success': False, 'error': 'This coupon has expired or reached its usage limit.'})

    cart = Cart.objects.get(user=request.user, is_active=True)

    if coupon.minimum_purchase_amount and cart.total_price < coupon.minimum_purchase_amount:
        return JsonResponse({
            'success': False,
            'error': f'Minimum purchase amount of ₹{coupon.minimum_purchase_amount} not met.'
        })

    # Check if a coupon is already applied
    if hasattr(cart, 'applied_coupon'):
        return JsonResponse({'success': False, 'error': 'A coupon has already been applied to your cart.'})

    # Calculate the discount
    if coupon.is_percentage:
        discount = Decimal(cart.total_price) * (coupon.discount / Decimal('100'))
    else:
        discount = min(coupon.discount, cart.total_price)  # Ensure discount doesn't exceed cart total

    # Apply the discount
    new_total = max(Decimal('0'), cart.total_price - discount)  # Ensure total doesn't go below 0
    
    # Store the applied coupon information on the cart
    cart.applied_coupon = coupon.code
    cart.applied_discount = discount
    cart.total_price = new_total
    cart.save()

    # Update coupon usage
    coupon.times_used += 1
    coupon.save()

    return JsonResponse({
        'success': True,
        'cart_total': str(new_total),
        'discount': str(discount)
    })

@require_POST
def remove_coupon(request):
    cart = Cart.objects.get(user=request.user, is_active=True)
    
    if not hasattr(cart, 'applied_coupon'):
        return JsonResponse({'success': False, 'error': 'No coupon applied to this cart.'})

    try:
        coupon = Coupon.objects.get(code=cart.applied_coupon)
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'Applied coupon not found.'})

    # Restore the original total
    new_total = cart.total_price + cart.applied_discount

    # Remove the coupon information from the cart
    cart.applied_coupon = None
    cart.applied_discount = Decimal('0')
    cart.total_price = new_total
    cart.save()

    # Update coupon usage
    coupon.times_used -= 1
    coupon.save()

    return JsonResponse({
        'success': True,
        'cart_total': str(new_total)
    })