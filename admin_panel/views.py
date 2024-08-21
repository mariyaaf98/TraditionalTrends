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
from datetime import datetime, timedelta,date
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

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
    return redirect('admin_panel:admin-login')

@login_required(login_url='/admin-panel/login/')
def users_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    user_details = User.objects.all().filter(is_superuser=False)

    return render(request, "admin_side/userslist.html", {"user_details": user_details})


@login_required(login_url='/admin-panel/login/')
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
    # Basic metrics
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

    # Latest orders
    latest_orders = Order.objects.order_by('-date')[:10]

    # Top 10 best-selling products
    best_selling_products = (OrderItem.objects
                             .values('variant__product__product_name')
                             .annotate(total_sold=Sum('quantity'))
                             .order_by('-total_sold')[:10])

    # Top 10 best-selling categories
    best_selling_categories = (OrderItem.objects
                               .values('variant__product__product_category__category_name')
                               .annotate(total_sold=Sum('quantity'))
                               .order_by('-total_sold')[:10])

    # Top 10 best-selling brands
    best_selling_brands = (OrderItem.objects
                       .values('variant__product__product_brand__brand_name')
                       .annotate(total_sold=Sum('quantity'))
                       .order_by('-total_sold')[:10])

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
        'best_selling_products': best_selling_products,
        'best_selling_categories': best_selling_categories,
        'best_selling_brands': best_selling_brands,
    }

    return render(request, 'admin_side/index.html', context)


@login_required(login_url='/admin-panel/login/')
def sales_report(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin-login")
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.filter(order_status="Delivered").order_by('-date')
    
    # Filter by date range if both start_date and end_date are provided
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            # Add one day to end_date to include the end date in the results
            end_date = end_date + timedelta(days=1)
            orders = orders.filter(date__range=[start_date, end_date])
        except ValueError:
            # If date parsing fails, reset the filter
            start_date = None
            end_date = None
    
    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Convert back to string for form display
    start_date_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, date) else ''
    end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, date) else ''
    
    # Render the template
    return render(request, 'admin_side/salesreport.html', {
        'page_obj': page_obj,
        'orders': page_obj,  # Add this line
        'start_date': start_date_str,
        'end_date': end_date_str,
    })



