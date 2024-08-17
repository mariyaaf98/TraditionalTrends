from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order, OrderItem,Wallet,Transaction,Return
from django.contrib import messages
from datetime import timedelta
from django.db import transaction
from .models import Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
import razorpay,json
from django.conf import settings
from cart_management.models import Cart, CartItem
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from coupon_management.models import Coupon,UserCoupon
from decimal import Decimal
from django.http import HttpResponse
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.utils import timezone
from .models import Order, OrderItem 
from reportlab.lib.units import inch


# @login_required
# def order_success(request):
#     try:
#         if not request.user.is_authenticated:
#             messages.error(request, "Please log in to view your order.")
#             return redirect('login')
        
#         # Fetch the most recent order for the logged-in user
#         order = Order.objects.filter(user=request.user, order_status='Processing').order_by('-date').first()
#         if not order:
#             raise Order.DoesNotExist

#         # Fetch order items
#         order_items = OrderItem.objects.filter(main_order=order)
#         arrival_date = order.date + timezone.timedelta(days=5)
#         if order.order_status == 'Cancelled':
#             arrival_date = None

#         # Calculate total price from order items
#         total_price = sum(Decimal(item.variant.product.offer_price) * item.quantity for item in order_items)

#         # Check if a coupon was applied to the order
#         user_coupon = UserCoupon.objects.filter(user=request.user, order=order, used=True).first()
#         discount = Decimal('0.00')
#         if user_coupon:
#             coupon = user_coupon.coupon
#             if coupon.is_percentage:
#                 discount = (coupon.discount / Decimal('100')) * total_price
#             else:
#                 discount = coupon.discount

#         # Calculate the final amount after applying the discount
#         final_amount = total_price - discount if user_coupon else total_price

#         context = {
#             'order': order,
#             'order_items': order_items,
#             'arrival_date': arrival_date,
#             'discount': discount,
#             'final_amount': final_amount,
#             'total_price': total_price,
#             'coupon_applied': user_coupon is not None,
#         }
#         return render(request, 'user_side/order_success.html', context)

#     except Order.DoesNotExist:
#         messages.error(request, "No recent order found.")
#         return redirect('cart_management:cart')



@login_required
def order_success(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to view your order.")
            return redirect('login')
        
        # Fetch the most recent order for the logged-in user
        order = Order.objects.filter(user=request.user, order_status='Processing').order_by('-date').first()
        if not order:
            raise Order.DoesNotExist

        # Fetch order items
        order_items = OrderItem.objects.filter(main_order=order)
        arrival_date = order.date + timezone.timedelta(days=5)
        if order.order_status == 'Cancelled':
            arrival_date = None

        # Calculate total price from order items
        total_price = sum(item.variant.product.offer_price * item.quantity for item in order_items)

        # Get the applied discount
        discount = order.coupon_discount or Decimal('0.00')

        # Calculate the final amount after applying the discount
        final_amount = total_price - discount

        context = {
            'order': order,
            'order_items': order_items,
            'arrival_date': arrival_date,
            'discount': discount,
            'final_amount': final_amount,
            'total_price': total_price,
            'coupon_applied': discount > Decimal('0.00'),
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
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(main_order=order)

    # Calculate subtotal (before coupon discount)
    subtotal = sum(item.total_cost() for item in order_items)

    # Fetch return information for each order item
    for item in order_items:
        item.return_info = Return.objects.filter(order_item=item).first()
    
    # Get user's wallet
    wallet = Wallet.objects.filter(user=request.user).first()

    # Fetch the applied coupon using UserCoupon model
    user_coupon = UserCoupon.objects.filter(order=order, user=request.user).first()
    coupon = user_coupon.coupon if user_coupon else None

    # Compute discount amount
    discount_amount = Decimal('0.00')
    if coupon:
        if coupon.is_percentage:
            discount_amount = subtotal * (Decimal(coupon.discount) / Decimal('100'))
        else:
            discount_amount = min(Decimal(coupon.discount), subtotal)  # Ensure discount doesn't exceed subtotal

    # Calculate the final total after discount
    final_total = subtotal - discount_amount

    context = {
        'order': order,
        'order_items': order_items,
        'wallet': wallet,
        'coupon': coupon,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }
    return render(request, 'user_side/order_detail.html', context)

@login_required
@require_POST
@transaction.atomic
def cancel_order_item(request, item_id):
    try:
        order_item = OrderItem.objects.select_for_update().get(id=item_id)
        variant = order_item.variant
        order = order_item.main_order

        # Calculate refund amount
        refund_amount = order_item.total_cost()

        # Check if a coupon was used for the order
        user_coupon = UserCoupon.objects.filter(order=order, user=order.user, used=True).first()
        if user_coupon:
            coupon = user_coupon.coupon
            if coupon.is_valid():  # Ensure the coupon is valid
                discount_amount = Decimal(coupon.discount)
                if coupon.is_percentage:
                    discount_amount = refund_amount * (discount_amount / Decimal('100'))
                refund_amount -= discount_amount

        # Ensure refund amount is not negative
        refund_amount = max(refund_amount, Decimal('0.00'))

        # Update variant stock and order item status
        variant.variant_stock += order_item.quantity
        variant.save()

        order_item.is_active = False
        order_item.save()

        # Check if all items in the order are canceled
        if not OrderItem.objects.filter(main_order=order, is_active=True).exists():
            order.order_status = 'Cancelled'
            order.save()

        # Refund to wallet
        if (order.payment_option == 'Online Payment' or order.payment_option == 'Wallet') and refund_amount > 0:
            wallet, created = Wallet.objects.get_or_create(user=order.user)
            wallet.credit(refund_amount)

        return JsonResponse({'success': True, 'refunded_amount': float(refund_amount)})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order item does not exist.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# @login_required
# def admin_order_list(request):
#     all_orders = Order.objects.all().select_related('user').prefetch_related('items', 'items__returns')

#     # Get orders with pending return requests
#     pending_returns = all_orders.filter(
#         items__returns__status='REQUESTED',
#         items__returns__requested_date__isnull=False
#     ).distinct().order_by('-items__returns__requested_date')[:10]

#     # Get all other orders (including those with non-pending returns)
#     other_orders = all_orders.exclude(
#     id__in=pending_returns.values_list('id', flat=True)).order_by('-date')

#     # Update payment status for orders with status 'Delivered'
#     for order in all_orders:
#         if order.order_status == 'Delivered':
#             order.payment_status = True
#             order.save()
            
#     context = {
#         'pending_returns': pending_returns,
#         'other_orders': other_orders,
#     }
#     return render(request, 'admin_side/orders-list.html', context)

@login_required
def admin_order_list(request):
    pending_returns = []
    other_orders = []

    for order in Order.objects.all().order_by('-date'):
        has_pending_return = False
        for item in order.items.all():
            for return_request in item.returns.filter(status='REQUESTED'):
                pending_returns.append({
                    'order': order,
                    'item': item,
                    'return_request': return_request
                })
                has_pending_return = True
        
        if not has_pending_return:
            other_orders.append(order)

    context = {
        'pending_returns': pending_returns,
        'other_orders': other_orders,
    }
    return render(request, 'admin_side/orders-list.html', context)


def return_order_list(request):
    # Fetch orders that have return requests, ordering by date
    orders = Order.objects.filter(items__returns__isnull=False).distinct().order_by('-date').prefetch_related('items__variant__product')
    
    # Paginate the orders
    paginator = Paginator(orders, 3)  
    page_number = request.GET.get('page', 1) 
    try:
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        page_obj = paginator.get_page(1)  
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'admin_side/return_orders.html', context)


@login_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(main_order=order).select_related('main_order').prefetch_related('returns')

    order.is_paid = (order.order_status == 'Delivered' or order.payment_status or order.payment_option in ['Wallet', 'Online Payment'])

    # Fetch return information for each order item
    for item in order_items:
        item.return_info = item.returns.first()  # Assumes one return per item

    item_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity']
    total_price = sum(item.total_cost() for item in order_items)
    
    context = {
        'order': order,
        'order_items': order_items,
        'item_quantity': item_quantity,
        'total_price': total_price,
    }

    return render(request, 'admin_side/order_detail.html', context)


@login_required
def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('order_status')

        if order.order_status not in ['Delivered', 'Cancelled']:
            if new_status in ['Processing', 'Shipped', 'Delivered', 'Cancelled']:
                if new_status == 'Cancelled':
                    # If the new status is 'Cancelled', update the stock of each item
                    order_items = OrderItem.objects.filter(main_order=order)
                    for order_item in order_items:
                        variant = order_item.variant
                        variant.variant_stock += order_item.quantity
                        variant.save()
                order.order_status = new_status
                order.save()
    
    return redirect('order_management:admin-order-detail', order_id=order.id)


@login_required
@require_POST
@transaction.atomic
def request_return(request, item_id):
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')
        
        order_item = OrderItem.objects.get(id=item_id)

        # Check if the order item is valid for return
        if order_item.main_order.order_status == 'Delivered' and not Return.objects.filter(order_item=order_item).exists():
        
            Return.objects.create(
                order_item=order_item,
                user=request.user,
                reason=reason,
                status='REQUESTED'
            )
            
            return JsonResponse({'success': True, 'message': 'Return requested successfully.'})
        else:
            return JsonResponse({'success': False, 'error': 'Unable to request return for this item.'})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order item not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@login_required
@require_POST
def process_return(request, return_id):
    action = request.POST.get('action')
    return_request = get_object_or_404(Return, id=return_id)

    if action == 'approve':
        return_request.status = 'APPROVED'
        return_request.processed_date = timezone.now()

        # Retrieve the order item and calculate the total refund amount
        order_item = return_request.order_item
        price = Decimal(order_item.unit_price)  # Ensure price is Decimal
        quantity = order_item.quantity
        total_refund = price * quantity

        # Check if a coupon was applied to the order
        order = order_item.main_order
        user_coupon = UserCoupon.objects.filter(order=order, user=return_request.user, used=True).first()
        if user_coupon:
            coupon = user_coupon.coupon
            if coupon.is_valid():
                # Calculate the discount based on the coupon type
                discount_amount = Decimal(coupon.discount)
                if coupon.is_percentage:
                    discount_amount = total_refund * (discount_amount / Decimal('100'))
                # Apply the discount to the total refund
                total_refund -= min(discount_amount, total_refund)

        # Ensure total refund is not negative
        total_refund = max(total_refund, Decimal('0.00'))

        # Add the total refund amount to the user's wallet
        wallet, created = Wallet.objects.get_or_create(user=return_request.user)
        wallet.balance = Decimal(wallet.balance) + total_refund  # Ensure balance is Decimal
        wallet.save()

        # Create a new transaction record with a clear description
        Transaction.objects.create(
            user=return_request.user,
            amount=total_refund,
            transaction_type='credit',
            description=f'Refund for return request #{return_request.id}',
            date=timezone.now()
        )

        return_request.save()
        messages.success(request, f'Return request #{return_id} approved.')

    elif action == 'reject':
        return_request.status = 'REJECTED'
        return_request.processed_date = timezone.now()
        return_request.save()
        messages.success(request, f'Return request #{return_id} rejected.')

    return redirect('order_management:admin-order-list')



@login_required
@csrf_exempt
def razorpay_callback(request):
    print('hi')
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
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
        order.order_status = 'Processing'  # Changed from 'Order Placed' to match other payment methods
        order.save()
        
        cart = Cart.objects.filter(user=order.user, is_active=True).first()
        if cart:
            CartItem.objects.filter(cart=cart).delete()
            cart.is_active = False
            cart.save()
        
        # Remove applied coupon from session
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
        
        # Apply coupon if used
        coupon = order.coupon_discount and Coupon.objects.filter(discount=order.coupon_discount).first()
        if coupon:
            UserCoupon.objects.create(
                user=order.user,
                coupon=coupon,
                used=True,
                used_at=timezone.now(),
                order=order
            )
        
        return redirect(reverse('order_management:order-success') + f'?order_id={order.id}')
    
    return HttpResponse("Method not allowed", status=405)


@login_required
def user_wallet_view(request):
    user = request.user

    # Try to get the wallet; if not found,
    try:
        wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        # Handle the case where the wallet does not exist
        messages.error(request, "No wallet found for the user.")
        return redirect('user_panel:user-profile') 

    transactions_list = Transaction.objects.filter(user=user).order_by('-date')
    
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    
    try:
        transactions = paginator.page(page_number)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    
    return render(request, 'user_side/wallet.html', context)

@login_required
def download_invoice(request, order_id):
    try:
        # Get the order object and related items
        order = get_object_or_404(Order, id=order_id)
        order_items = OrderItem.objects.filter(main_order=order)

        buffer = BytesIO()

        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = ParagraphStyle(name="Subtitle", fontSize=14, leading=18, spaceAfter=12)
            normal_style = styles['Normal']

            elements.append(Paragraph("TraditionalTrends", title_style))
            elements.append(Paragraph("INVOICE", subtitle_style))
            elements.append(Spacer(1, 0.5 * inch))

            # Populate invoice details
            elements.append(Paragraph(f"<b>Order Number:</b> {order.order_id}", normal_style))
            elements.append(Paragraph(f"<b>Order Date:</b> {order.date.strftime('%B %d, %Y')}", normal_style))
            elements.append(Paragraph(f"<b>Customer Name:</b> {order.name}", normal_style))
            elements.append(Paragraph(f"<b>Email:</b> {order.user.email}", normal_style))
            elements.append(Paragraph(f"<b>Phone:</b> {order.phone_number}", normal_style))
            elements.append(Paragraph(f"<b>Address:</b> {order.house_name}, {order.street_name}, {order.district}, {order.state}, {order.pin_number}, {order.country}", normal_style))
            elements.append(Spacer(1, 0.5 * inch))

            # Prepare table data
            data = [['Product', 'Quantity', 'Unit Price', 'Total Price']]
            for item in order_items:
                data.append([
                    item.variant.product.product_name,
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.total_cost():.2f}"
                ])

            # Summary
            data.append(['', '', 'Subtotal:', f"{order.total_amount:.2f}"])
            data.append(['', '', 'Discount:', f"{order.coupon_discount or 0:.2f}"])
            data.append(['', '', 'Shipping:', 'Free'])
            data.append(['', '', 'Total:', f"{order.total_amount - (order.coupon_discount or 0):.2f}"])

            # Create and style the table
            table = Table(data, colWidths=[2.5 * inch, 1.25 * inch, 1.25 * inch, 1.5 * inch])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (2, -4), (-1, -2), colors.lightgrey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
            ])
            table.setStyle(style)
            elements.append(table)

            # Footer Note
            elements.append(Spacer(1, 1 * inch))
            elements.append(Paragraph("Thank you for shopping with TraditionalTrends!", normal_style))

            doc.build(elements)
        except Exception as e:
            return HttpResponse(f'Error generating PDF content: {str(e)}', status=500)

        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename=f'invoice_{order_id}.pdf')

    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)