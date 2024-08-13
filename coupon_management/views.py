from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from . models import Coupon
from cart_management . models import Cart
from .forms import CouponForm
import logging
import random
import string
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
import json
from django.http import JsonResponse, Http404



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
            return redirect('coupon_management:coupon-list') 
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
            return redirect('coupon_management:coupon-list')
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
    return redirect('coupon_management:coupon_list')



# @require_POST
# def apply_coupon(request):
#     try:
#         data = json.loads(request.body)
#         coupon_code = data.get('coupon_code')
        
#         coupon = get_object_or_404(Coupon, code=coupon_code)
#         cart = Cart.objects.get(user=request.user, is_active=True)

#         # Validate coupon
#         if not coupon.is_valid():
#             return JsonResponse({'status': 'error', 'message': 'This coupon is not valid.'})
        
#         if coupon.user and coupon.user != request.user:
#             return JsonResponse({'status': 'error', 'message': 'This coupon is not valid for your account.'})
        
#         cart_total = cart.get_total_price()

#         # Check minimum purchase amount
#         if cart_total < coupon.minimum_purchase_amount:
#             return JsonResponse({
#                 'status': 'error', 
#                 'message': f'Minimum purchase amount of ₹{coupon.minimum_purchase_amount} required for this coupon.'
#             })

#         # Calculate discount
#         if coupon.is_percentage:
#             discount_amount = (cart_total * coupon.discount) / 100
#         else:
#             discount_amount = coupon.discount

#         # Ensure discount doesn't exceed cart total
#         discount_amount = min(discount_amount, cart_total)
#         new_total = cart_total - discount_amount
        
#         # Apply coupon to cart
#         cart.applied_coupon = coupon
#         cart.save()

#         # Update coupon usage
#         coupon.times_used += 1
#         coupon.save()
        
#         return JsonResponse({
#             'status': 'success',
#             'message': 'Coupon applied successfully!',
#             'coupon_code': coupon.code,
#             'discount': str(discount_amount),
#             'new_total': str(new_total)
#         })
              
#     except Http404:
#         return JsonResponse({'status': 'error', 'message': 'Invalid coupon code or cart not found.'})
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)})

# @require_POST
# def apply_coupon(request):
#     try:
#         data = json.loads(request.body)
#         coupon_code = data.get('coupon_code')
        
#         coupon = get_object_or_404(Coupon, code=coupon_code)
#         cart = Cart.objects.get(user=request.user, is_active=True)

#         # Validate coupon
#         if not coupon.is_valid():
#             return JsonResponse({'status': 'error', 'message': 'This coupon is not valid.'})
        
#         if coupon.user and coupon.user != request.user:
#             return JsonResponse({'status': 'error', 'message': 'This coupon is not valid for your account.'})
        
#         cart_total = cart.get_total_price()

#         # Check minimum purchase amount
#         if cart_total < coupon.minimum_purchase_amount:
#             return JsonResponse({
#                 'status': 'error', 
#                 'message': f'Minimum purchase amount of ₹{coupon.minimum_purchase_amount} required for this coupon.'
#             })

#         # Calculate discount
#         if coupon.is_percentage:
#             discount_amount = (cart_total * coupon.discount) / 100
#         else:
#             discount_amount = coupon.discount

#         # Ensure discount doesn't exceed cart total
#         discount_amount = min(discount_amount, cart_total)
#         new_total = cart_total - discount_amount
        
#         # Apply coupon to cart
#         cart.applied_coupon = coupon
#         cart.save()
        
#         return JsonResponse({
#             'status': 'success',
#             'message': 'Coupon applied successfully!',
#             'coupon_code': coupon.code,
#             'discount': str(discount_amount),
#             'new_total': str(new_total)
#         })
              
#     except Http404:
#         return JsonResponse({'status': 'error', 'message': 'Invalid coupon code or cart not found.'})
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)})



@require_POST
def apply_coupon(request):
    # Retrieve user ID from the session
    user_id = request.session.get('user_id')
    if user_id is None:
        return JsonResponse({
            'status': 'error',
            'message': 'User not authenticated.'
        })

    data = json.loads(request.body)
    coupon_code = data.get('coupon_code')
    cart = Cart.objects.get(user=request.user, is_active=True)
    total_price = cart.get_total_price()

    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        if not coupon.is_valid():
            raise Coupon.DoesNotExist
        
        # Check minimum purchase amount
        if total_price < coupon.minimum_purchase_amount:
            return JsonResponse({
                'status': 'error', 
                'message': f'Minimum purchase amount of ₹{coupon.minimum_purchase_amount} required for this coupon.'
            })

        discount = coupon.discount
        if coupon.is_percentage:
            discount = (discount / Decimal('100')) * total_price

        new_total = total_price - discount

        # Convert Decimal objects to float or str
        new_total = float(new_total)  # or str(new_total)
        discount = float(discount)  # or str(discount)

        # Store the coupon in the session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount': discount,
            'new_total': new_total,
        }

        return JsonResponse({
            'status': 'success',
            'new_total': str(new_total),  # Alternatively use float(new_total)
            'discount': str(discount),    # Alternatively use float(discount)
            'message': 'Coupon applied successfully!'
        })

    except Coupon.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid or expired coupon.'
        })

@require_POST
def remove_coupon(request):
    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        original_total = cart.get_total_price()
        
        # Remove the applied coupon from session
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
        
        return JsonResponse({
            'status': 'success',
            'message': 'Coupon removed successfully!',
            'new_total': str(original_total)
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No active cart found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    




# @require_POST
# def remove_coupon(request):
#     try:
#         cart = Cart.objects.get(user=request.user, is_active=True)
        
#         # Remove the applied coupon
#         cart.applied_coupon = None
#         cart.save()
        
#         # Recalculate the cart total without the coupon
#         original_total = cart.get_total_price()  # Assuming get_total_price() returns the total without any coupon

#         return JsonResponse({
#             'status': 'success',
#             'message': 'Coupon removed successfully!',
#             'new_total': str(original_total)
#         })
#     except Cart.DoesNotExist:
#         return JsonResponse({'status': 'error', 'message': 'Cart not found.'})
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)})

