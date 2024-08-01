from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order, OrderItem,Wallet,Transaction
from django.contrib import messages
from datetime import timedelta
from django.db import transaction
from .models import Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
import razorpay
from django.conf import settings
from cart_management.models import Cart, CartItem
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.paginator import Paginator


@login_required
def order_success(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to view your order.")
            return redirect('login')
        
        # Fetch the most recent order for the logged-in user
        order = Order.objects.filter(user=request.user, order_status='Order Placed').order_by('-date').first()
        if not order:
            raise Order.DoesNotExist

        # Fetch order items
        order_items = OrderItem.objects.filter(main_order=order)
        arrival_date = order.date + timezone.timedelta(days=5)
        if order.order_status == 'Cancelled':
            arrival_date = None

        context = {
            'order': order,
            'order_items': order_items,
            'arrival_date': arrival_date,
        }
        return render(request, 'user_side/order_success.html', context)

    except Order.DoesNotExist:
        messages.error(request, "No recent order found.")
        return redirect('cart_management:cart')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-date')
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    estimated_delivery_days = 5 
    arrival_date = timezone.now() + timedelta(days=estimated_delivery_days)

    context = {
        'page_obj': page_obj,
        'arrival_date': arrival_date,
    }
    return render(request, 'user_side/order_list.html', context)


@login_required
def user_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    order_items = OrderItem.objects.filter(main_order=order)
    
    wallet = Wallet.objects.filter(user=request.user).first()

    context = {
        'order': order,
        'order_items': order_items,
        'wallet': wallet,
    }
    return render(request, 'user_side/order_detail.html', context)

@require_POST
@transaction.atomic
def cancel_order_item(request, item_id):
    try:
        order_item = OrderItem.objects.select_for_update().get(id=item_id)
        variant = order_item.variant
        order = order_item.main_order

        refund_amount = order_item.total_cost()
        variant.variant_stock += order_item.quantity
        variant.save()

        order_item.is_active = False
        order_item.save()

        # Check if all items in the order are canceled
        if not OrderItem.objects.filter(main_order=order, is_active=True).exists():
            order.order_status = 'Cancelled'
            order.save()

        # Refund to wallet if the payment was online
        if order.payment_option == 'Online Payment' and refund_amount > 0:
            wallet, created = Wallet.objects.get_or_create(user=order.user)
            wallet.credit(refund_amount)

        return JsonResponse({'success': True, 'refunded_amount': float(refund_amount)})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order item does not exist.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def admin_order_list(request):
    orders = Order.objects.all().order_by('-date')
    order_items = OrderItem.objects.filter(main_order__in=orders, is_active=True)

    context = {
        'orders': orders,
        'order_items': order_items,
    }
    return render(request, 'admin_side/orders-list.html', context)


def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(main_order=order)
    
    item_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity']
    total_price = sum(item.total_cost() for item in order_items)
    
    context = {
        'order': order,
        'order_items': order_items,
        'item_quantity': item_quantity, 
        'total_price': total_price,    
    }

    return render(request, 'admin_side/order_detail.html', context)


def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('order_status')

        if new_status in ['Processing', 'Shipped', 'Delivered', 'Cancelled']:
            if order.order_status != 'Cancelled':
                if new_status == 'Cancelled':
                    #new status is 'Cancelled', update the stock of each item
                    order_items = OrderItem.objects.filter(main_order=order)
                    for order_item in order_items:
                        variant = order_item.variant
                        variant.variant_stock += order_item.quantity
                        variant.save()
                order.order_status = new_status
                order.save()
    
    return redirect('order_management:admin-order-detail', order_id=order.id)


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        except Order.DoesNotExist:
            return HttpResponse("Order not found", status=400)
        
        # Verify the payment signature
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return HttpResponse("Invalid signature", status=400)
        
        order.payment_status = True
        order.payment_id = payment_id
        order.order_status = 'Order Placed'
        order.save()
        
        
        cart = Cart.objects.filter(user=order.user, is_active=True).first()
        if cart:
            CartItem.objects.filter(cart=cart).delete()
            cart.is_active = False
            cart.save()
        
       
        return redirect(reverse('order_management:order-success') + f'?order_id={order.id}')
    
    return HttpResponse("Method not allowed", status=405)



def user_wallet_view(request):
    user = request.user 
    wallet = get_object_or_404(Wallet, user=user)
    transactions =Transaction.objects.filter(user=request.user)
    context = {
        'wallet': wallet,
        'transactions':transactions,
    }
    
    return render(request, 'user_side/wallet.html', context)