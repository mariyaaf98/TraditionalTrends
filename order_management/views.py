from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order, OrderItem
from cart_management.models import CartItem
from django.contrib import messages
import datetime 
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from cart_management.models import Cart, CartItem
from django.db import transaction
from .models import Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST




@login_required
def order_success(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to view your order.")
            return redirect('login')  # Replace 'login' with your actual login URL name

        order = Order.objects.filter(user=request.user, order_status='Order Placed').order_by('-date').first()
        if not order:
            raise Order.DoesNotExist

        order_items = OrderItem.objects.filter(main_order=order)
        print(order_items)

        arrival_date = order.date + timezone.timedelta(days=5)

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
    order_items = OrderItem.objects.filter(Q(user=request.user) & Q(is_active=True))

    estimated_delivery_days = 5 
    arrival_date = now() + timedelta(days=estimated_delivery_days)

    context={
        'orders': orders,
        'order_items ':order_items ,
        'arrival_date':arrival_date,
        }
    return render(request, 'user_side/order_list.html', context)


@require_POST
@transaction.atomic
def cancel_order_item(request, item_id):
    try:
        order_item = OrderItem.objects.get(id=item_id)
        variant = order_item.variant
        
        # Revert the stock
        variant.variant_stock += order_item.quantity
        variant.save()

        # Mark the item as inactive (canceled)
        order_item.is_active = False
        order_item.save()

        return JsonResponse({'success': True})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order item does not exist.'})


