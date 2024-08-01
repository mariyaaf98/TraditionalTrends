from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from cart_management.models import Cart, CartItem
from product_management.models import Product_Variant, Products
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user_panel.models import Address
from django.contrib import messages
from order_management.models import Order,OrderItem,Wallet
import datetime 
from django.utils.timezone import now
from datetime import timedelta
import re
import razorpay
from django.conf import settings
from django.urls import reverse
import logging

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
            return JsonResponse({'error': 'Currectly Unavilable'}, status=400)
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

    cart_total = sum(
        item.quantity * (item.variant.product.offer_price if item.variant else item.product.offer_price)
        for item in cart_items
    )

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
    
    MAX_QUANTITY = 5  

    quantity = int(request.POST.get('quantity', 1))

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__is_active=True)
    variant = cart_item.variant

    # Check if the requested quantity exceeds the maximum allowed
    if quantity > MAX_QUANTITY:
        return JsonResponse({'error': f'Maximum quantity of {MAX_QUANTITY} items per product allowed.'}, status=400)

    # Check if the requested quantity exceeds available stock
    if variant and quantity > variant.variant_stock:
        return JsonResponse({'error': 'This item is currently unavailable in the requested quantity.'}, status=400)

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



logger = logging.getLogger(__name__)
@login_required
@transaction.atomic
def checkout(request):
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty. Please add items before proceeding to checkout.")
        return redirect('cart_management:cart')

    total_price = sum(item.variant.product.offer_price * item.quantity for item in cart_items)
    
    # check stock and product avilabilities
    for item in cart_items:
        if item.quantity > item.variant.variant_stock:
            messages.error(request, f"Insufficient stock for {item.variant.product.product_name}.")
            return redirect('cart_management:cart')
        if item.variant.product.is_deleted or item.variant.is_deleted:
            messages.error(request, f"{item.variant.product.product_name} is no longer available.")
            return redirect('cart_management:cart')

    address_list = Address.objects.filter(user=request.user)
    selected_address = address_list.filter(default=True).first()

    estimated_delivery_days = 5  
    arrival_date = now() + timedelta(days=estimated_delivery_days)

    if request.method == 'POST':
        if 'place_order' in request.POST:
            if cart_items.exists():
                payment_method = request.POST.get('payment_method')
                if not payment_method:
                    messages.error(request, "Please select a payment method.")
                    return redirect('cart_management:checkout')

                if not selected_address:
                    messages.error(request, "Please select a delivery address.")
                    return redirect('cart_management:checkout')

                try:
                    with transaction.atomic():
                        # Stock check and update variant quantities
                        for item in cart_items:
                            variant = item.variant
                            if variant.variant_stock < item.quantity:
                                messages.error(request, f'Not enough stock for {variant.product.product_name} - {variant.colour_name}')
                                return redirect('cart_management:checkout')

                            variant.variant_stock -= item.quantity
                            variant.save()

                        order = Order.objects.create(
                            user=request.user,
                            total_amount=total_price,
                            payment_option=payment_method,
                            name=selected_address.name,
                            house_name=selected_address.house_name,
                            street_name=selected_address.street_name,
                            pin_number=selected_address.pin_number,
                            district=selected_address.district,
                            state=selected_address.state,
                            country=selected_address.country,
                            phone_number=selected_address.phone_number,
                            order_id=f"ORDER-{now().strftime('%Y%m%d%H%M%S')}-{request.user.id}"
                        )

                        for item in cart_items:
                            OrderItem.objects.create(
                                main_order=order,
                                variant=item.variant,
                                quantity=item.quantity,
                                user=request.user,
                                is_active=True
                            )

                        if payment_method == 'Online Payment':
                            # Create Razorpay Order
                            razorpay_order = razorpay_client.order.create(dict(
                                amount=int(total_price * 100),
                                currency='INR',
                                payment_capture='1'
                            ))

                    
                            order.razorpay_order_id = razorpay_order['id']
                            order.save()

                        
                            razorpay_payment = {
                                'razorpay_key': settings.RAZORPAY_KEY_ID,
                                'razorpay_order_id': razorpay_order['id'],
                                'razorpay_amount': int(total_price * 100),
                                'currency': 'INR',
                                'callback_url': request.build_absolute_uri(reverse('order_management:razorpay-callback'))
                            }

                            return render(request, 'user_side/razorpay_payment.html', {'razorpay_payment': razorpay_payment})
                        elif payment_method == 'Wallet':
                            # Check if user has a wallet
                            wallet, created = Wallet.objects.get_or_create(user=request.user)
                            if wallet.is_sufficient(total_price):
                                # Deduct amount from wallet
                                wallet.debit(total_price)

                                # Update order status
                                order.payment_status = True
                                order.order_status = 'Processing'
                                order.save()

                                CartItem.objects.filter(cart=cart).delete()
                                cart.is_active = False
                                cart.save()

                                messages.success(request, "Payment successful. Your order has been placed.")
                                return redirect('order_management:order-success')
                            else:
                                messages.error(request, "Insufficient wallet balance. Please choose another payment method.")
                                return redirect('cart_management:checkout')
                        else:
                            # Cash on Delivery or other payment methods
                            CartItem.objects.filter(cart=cart).delete()
                            cart.is_active = False
                            cart.save()

                            messages.success(request, "Your order has been placed successfully!")
                            return redirect('order_management:order-success')
                except Exception as e:
                    logger.error(f"Order placement failed for user {request.user.id}: {str(e)}", exc_info=True)
                    messages.error(request, "Failed to place the order. Please try again later.")
                    return redirect('cart_management:checkout')
            else:
                messages.error(request, "Your cart is empty. Please add items before placing an order.")
                return redirect('cart_management:cart')

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'address_list': address_list,
        'selected_address': selected_address,
        'payment_methods': ['Cash on Delivery', 'Online Payment', 'Wallet'],
        'arrival_date': arrival_date,
    }

    return render(request, 'user_side/checkout.html', context)




@require_POST
@login_required
def update_default_address(request):
    address_id = request.POST.get('address_id')
    if address_id:
        try:
            new_default_address = Address.objects.get(id=address_id, user=request.user)
            # Unset current default address
            Address.objects.filter(user=request.user, default=True).update(default=False)
            # Set new default address
            new_default_address.default = True
            new_default_address.save()
            return JsonResponse({'status': 'success'})
        except Address.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid address selected.'})
    return JsonResponse({'status': 'error', 'message': 'No address selected.'})


@login_required
def checkout_add_address(request):
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        house_name = request.POST.get('house_name')
        street_name = request.POST.get('street_name')
        pin_number = request.POST.get('pin_number')
        district = request.POST.get('district')
        state = request.POST.get('state')
        country = request.POST.get('country')
        phone_number = request.POST.get('phone_number')
        default = 'default' in request.POST
        
        

        # Validate required fields
        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, 'All fields are required.')
            return redirect('cart_management:checkout-add-address')
        
        # Validate address fields
        pattern = r'^[A-Za-z\s]*$'
        if not (re.match(pattern, name) and re.match(pattern, house_name) and
                re.match(pattern, street_name) and re.match(pattern, district) and
                re.match(pattern, state) and re.match(pattern, country)):
            messages.error(request, 'Address fields should only contain letters and spaces.')
            return redirect('cart_management:checkout-add-address')
        
        # Validate phone number
        if not phone_number.isdigit() or int(phone_number) == 0:
            messages.error(request, 'Phone number must be numeric and cannot be all zeros.')
            return redirect('cart_management:checkout-add-address')
        
        # Create and save the new address
        address = Address(
            user=request.user,
            name=name,
            house_name=house_name,
            street_name=street_name,
            pin_number=pin_number,
            district=district,
            state=state,
            country=country,
            phone_number=phone_number,
            default=default
        )
        address.save()
        messages.success(request, 'Address added successfully!')
        return redirect('cart_management:checkout')  # Redirect to checkout or a relevant page

    return render(request, 'user_side/checkout.html', {'addresses': addresses})
