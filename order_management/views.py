from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order, OrderItem
from django.contrib import messages
from datetime import timedelta
from django.db import transaction
from .models import Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum

@login_required
def order_success(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to view your order.")
            return redirect('login')
        
        order = Order.objects.filter(user=request.user, order_status='Order Placed').order_by('-date').first()
        if not order:
            raise Order.DoesNotExist

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
    order_items = OrderItem.objects.filter(main_order__in=orders, is_active=True)
    
    estimated_delivery_days = 5 
    arrival_date = timezone.now() + timedelta(days=estimated_delivery_days)

    context = {
        'orders': orders,
        'order_items': order_items, 
        'arrival_date': arrival_date,
    }
    return render(request, 'user_side/order_list.html', context)


@require_POST
@transaction.atomic
def cancel_order_item(request, item_id):
    try:
        order_item = OrderItem.objects.get(id=item_id)
        variant = order_item.variant
        order = order_item.main_order

        # Revert the stock
        variant.variant_stock += order_item.quantity
        variant.save()

        # Update the order item status
        order_item.is_active = False
        order_item.save()

        # Check if all items in the order are cancelled
        if not OrderItem.objects.filter(main_order=order, is_active=True).exists():
            order.order_status = 'Cancelled'
            order.save()

        return JsonResponse({'success': True})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order item does not exist.'})



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
