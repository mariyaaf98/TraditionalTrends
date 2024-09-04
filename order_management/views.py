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
from coupon_management.models import UserCoupon
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
from decimal import Decimal
import razorpay

@login_required
def order_success(request):
    try:
        # Fetch the most recent order for the logged-in user
        order = Order.objects.filter(user=request.user).order_by('-date').first()

        if not order:
            messages.error(request, "No recent order found.")
            return redirect('cart_management:cart')

        # Check if the order is actually successful
        if (order.payment_status and order.order_status == 'Order Placed') or \
           (not order.payment_status and order.payment_option == 'Cash on Delivery' and order.order_status == 'Order Placed'):
            # Fetch order items
            order_items = OrderItem.objects.filter(main_order=order)
            arrival_date = order.date + timezone.timedelta(days=5)

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
        else:
            messages.error(request, "Your order was not completed successfully.")
            return redirect('order_management:order-failed')

    except Exception as e:
        logger.error(f"Error while processing order success for user {request.user.id}: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('cart_management:cart')


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).exclude(payment_status__isnull=True).exclude(payment_status='False').order_by('-date')
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

@login_required(login_url='user_login')
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
            if coupon.is_valid(): 
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



@login_required
def admin_order_list(request):
    pending_returns = []
    other_orders = []

    for order in Order.objects.exclude(payment_status__isnull=True).exclude(payment_status='False').order_by('-date'):
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


    # Paginate pending_returns
    pending_returns_paginator = Paginator(pending_returns, 10)  # Show 10 pending returns per page
    pending_returns_page_number = request.GET.get('pending_page')
    pending_returns_page_obj = pending_returns_paginator.get_page(pending_returns_page_number)

    # Paginate other_orders
    other_orders_paginator = Paginator(other_orders, 10)  # Show 10 orders per page
    other_orders_page_number = request.GET.get('orders_page')
    other_orders_page_obj = other_orders_paginator.get_page(other_orders_page_number)

    context = {
        'pending_returns': pending_returns_page_obj,
        'other_orders': other_orders_page_obj,
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
        item.return_info = item.returns.first()

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


@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        try:
            payment_data = request.POST
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Verify the payment signature
            params_dict = {
                'razorpay_order_id': payment_data['razorpay_order_id'],
                'razorpay_payment_id': payment_data['razorpay_payment_id'],
                'razorpay_signature': payment_data['razorpay_signature']
            }
            
            try:
                client.utility.verify_payment_signature(params_dict)
            except:
                messages.error(request, "Payment verification failed. Please try again.")
                return redirect('order_management:order-failed')
            
            # If verification is successful, fetch the order
            order = Order.objects.get(razorpay_order_id=payment_data['razorpay_order_id'])
            
            # Check if the payment was successful
            razorpay_payment_id = payment_data.get('razorpay_payment_id', None)
            if razorpay_payment_id:
                payment_capture_response = client.payment.fetch(razorpay_payment_id)
                
                if payment_capture_response['status'] == 'captured':
                    with transaction.atomic():
                        for item in order.items.all():
                            variant = item.variant
                            if variant.variant_stock < item.quantity:
                                raise ValueError(f"Insufficient stock for {variant.product.product_name}")
                            variant.variant_stock -= item.quantity
                            variant.save()
                        
                        order.payment_status = True
                        order.order_status = 'Order Placed'
                        order.save()

                        cart = Cart.objects.get(user=order.user, is_active=True)
                        CartItem.objects.filter(cart=cart).delete()
                        cart.is_active = False
                        cart.save()
                    
                    messages.success(request, "Payment successful. Your order is now processing.")
                    return redirect('order_management:order-success')
                else:
                    messages.error(request, "Payment failed. Please try again.")
                    return redirect('order_management:order-failed')
            else:
                messages.error(request, "Payment ID not found. Please try again.")
                return redirect('order_management:order-failed')
        
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('order_management:order-failed')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('order_management:order-failed')
        except Exception as e:
            logger.error(f"Error processing Razorpay callback: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred during payment processing. Please try again.")
            return redirect('order_management:order-failed')
    else:
        # Handle GET request (when user closes the payment window)
        razorpay_order_id = request.GET.get('razorpay_order_id')
        if razorpay_order_id:
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.order_status = 'Cancelled'
                order.save()
                messages.error(request, "Payment cancelled. Your order has been marked as cancelled.")
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
        else:
            messages.error(request, "Payment process was interrupted. Please try again.")
        return redirect('order_management:order-failed')




def order_failed(request):
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = Order.objects.filter(user=request.user).order_by('-date').first()

    if order:
        order.order_status = 'Pending'
        order.save()

    if order and order.payment_option == 'Online Payment':
        razorpay_order = razorpay_client.order.create(dict(
            amount=int(order.total_amount * 100),
            currency='INR',
            payment_capture='1'
        ))

        order.razorpay_order_id = razorpay_order['id']
        order.save()

        razorpay_payment = {
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_amount': int(order.total_amount * 100),
            'currency': 'INR',
            'callback_url': request.build_absolute_uri(reverse('order_management:razorpay-callback'))
        }
    else:
        razorpay_payment = None

    messages.error(request, "Your order was not completed successfully12334.")
    return render(request, 'user_side/order_failed.html', {'order': order, 'razorpay_payment': razorpay_payment})


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


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_razorpay_order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        amount = int(order.total_amount * 100)  # Convert to paisa (smallest unit)

        # Create a Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save the Razorpay order ID in your database
        order.razorpay_order_id = razorpay_order['id']
        order.save()

        return JsonResponse({
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_amount': amount,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'user_email': request.user.email,
            'user_name': request.user.get_full_name(),
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)