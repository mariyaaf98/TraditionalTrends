from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout,authenticate
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import AdminLoginForm
from accounts.models import User
from order_management.models import Order, OrderItem
from django.db.models import Sum, Avg
from django.utils import timezone
from product_management.models import Product_Variant, Products
from datetime import datetime

def is_admin(user):
    return user.is_superuser


def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None and user.is_superuser:
                login(request, user)
                return redirect('admin_panel:admin-index')
            else:
                messages.error(request, 'Invalid email or password')
    else:
        form = AdminLoginForm()
    return render(request, 'admin_side/login.html', {'form': form})

def admin_logout(request):
    logout(request)
    return redirect('admin_panel:admin_login')

def users_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    user_details = User.objects.all().filter(is_superuser=False)

    return render(request, "admin_side/userslist.html", {"user_details": user_details})

def block_unblock_user(request, id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin-login")

    try:
        user = User.objects.get(id=id)
        if user.is_active == False:
            user.is_active = True
            user.save()
        else:
            user.is_active = False
            user.save()

    except Exception:
        messages.warning("There is no such user")

    return redirect("admin_panel:users-list")


@user_passes_test(is_admin)
def admin_dashboard(request):
   
    total_revenue = Order.objects.filter(payment_status=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.exclude(order_status='Cancelled').count()
    total_products = Products.objects.count()
    total_categories = Products.objects.values('product_category').distinct().count()

    # Monthly earnings
    current_month = timezone.now().month
    monthly_earnings = Order.objects.filter(
        payment_status=True,
        date__month=current_month
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Sales data and labels for the chart
    sales_data = list(Order.objects.filter(payment_status=True)
                      .values('date__date')
                      .annotate(total_sales=Sum('total_amount'))
                      .order_by('date__date')
                      .values_list('total_sales', flat=True))

    sales_labels = list(Order.objects.filter(payment_status=True)
                        .values('date__date')
                        .annotate(total_sales=Sum('total_amount'))
                        .order_by('date__date')
                        .values_list('date__date', flat=True))

    sales_labels = [date.strftime('%Y-%m-%d') for date in sales_labels]

   
    total_sales = sum(sales_data)
    avg_order_value = Order.objects.filter(payment_status=True).aggregate(Avg('total_amount'))['total_amount__avg'] or 0

    conversion_rate = 65

    latest_orders = Order.objects.order_by('-date')[:10]
    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_categories': total_categories,
        'monthly_earnings': monthly_earnings,
        'sales_data': sales_data,
        'sales_labels': sales_labels,
        'total_sales': total_sales,
        'avg_order_value': round(avg_order_value, 2),
        'conversion_rate': conversion_rate,
        'latest_orders': latest_orders,
    }

    return render(request, 'admin_side/index.html', context)

def sales_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return redirect('admin_panel:sales-report')
            
            orders = Order.objects.filter(date__range=[start_date, end_date], order_status="Delivered")
            return render(request, 'admin_side/dashboard/salesreport.html', {'orders': orders})
    
    orders = Order.objects.filter(order_status="Delivered")
    return render(request, 'admin_side/salesreport.html', {'orders': orders})