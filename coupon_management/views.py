from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from . models import Coupon,UserCoupon
from cart_management . models import Cart
from .forms import CouponForm
import random
import string
from django.core.paginator import Paginator
from decimal import Decimal
import json
from django.http import JsonResponse


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
    paginator = Paginator(coupons, 20) 

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
        coupon.is_active = False 
        coupon.save()
        messages.success(request, 'Coupon delete successfully!')
        return redirect(request.META.get('HTTP_REFERER'))  
    return redirect('coupon_management:coupon_list')


@require_POST
def apply_coupon(request):
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
        
        # Check if the user has already used this coupon
        if UserCoupon.objects.filter(user=request.user, coupon=coupon, used=True).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'You have already used this coupon.'
            })

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
        # Convert Decimal objects to float 
        new_total = float(new_total)  
        discount = float(discount)  

        # Store the coupon in the session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount': discount,
            'new_total': new_total,
        }

        # Mark the coupon as used for this user
        UserCoupon.objects.create(user=request.user, coupon=coupon, used=False)

        return JsonResponse({
            'status': 'success',
            'new_total': str(new_total),
            'discount': str(discount),
            'message': 'Coupon applied successfully!'
        })

    except Coupon.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid or expired coupon.'
        })



@require_POST
@require_POST
def remove_coupon(request):
    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        original_total = cart.get_total_price()
        
        user_coupon = UserCoupon.objects.filter(user=request.user, used=False, order__isnull=True).first()

        if user_coupon:
            user_coupon.used = True
            user_coupon.order = None
            user_coupon.save()

            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

            return JsonResponse({
                'status': 'success',
                'message': 'Coupon removed successfully!',
                'new_total': str(original_total)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'No coupon was applied to your cart.'
            })

    except Cart.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No active cart found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    


