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
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Sum
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncDay
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.db.models import Count


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

    user_details = User.objects.filter(is_superuser=False)
    
    # Pagination
    paginator = Paginator(user_details, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "admin_side/userslist.html", {"page_obj": page_obj})


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

    # Yearly sales data
    current_year = timezone.now().year
    yearly_sales = (Order.objects.filter(payment_status=True, date__year=current_year)
                    .annotate(month=TruncMonth('date'))
                    .values('month')
                    .annotate(total_sales=Sum('total_amount'))
                    .order_by('month'))

    # Monthly sales data (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    monthly_sales = (Order.objects.filter(payment_status=True, date__gte=thirty_days_ago)
                     .annotate(day=TruncDay('date'))
                     .values('day')
                     .annotate(total_sales=Sum('total_amount'))
                     .order_by('day'))

    # Total sales and average order value
    total_sales = sum(sale['total_sales'] for sale in yearly_sales)
    avg_order_value = Order.objects.filter(payment_status=True).aggregate(Avg('total_amount'))['total_amount__avg'] or 0

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

    # Order status distribution
    order_status_distribution = (Order.objects
                                 .values('order_status')
                                 .annotate(count=Count('id'))
                                 .order_by('order_status'))

    # Prepare data for charts
    daily_sales = Order.objects.filter(payment_status=True)\
        .annotate(truncated_date=TruncDate('date'))\
        .values('truncated_date')\
        .annotate(total_sales=Sum('total_amount'))\
        .order_by('truncated_date')
    
    # Prepare data for top categories and brands
    top_categories = OrderItem.objects.values('variant__product__product_category__category_name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:5]
    
    top_brands = OrderItem.objects.values('variant__product__product_brand__brand_name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:5]

    # Prepare data for charts
    daily_sales_labels = [sale['truncated_date'].strftime('%Y-%m-%d') for sale in daily_sales]
    daily_sales_data = [float(sale['total_sales']) for sale in daily_sales]

    monthly_sales_labels = [sale['day'].strftime('%Y-%m-%d') for sale in monthly_sales]
    monthly_sales_data = [float(sale['total_sales']) for sale in monthly_sales]

    yearly_sales_labels = [sale['month'].strftime('%Y-%m') for sale in yearly_sales]
    yearly_sales_data = [float(sale['total_sales']) for sale in yearly_sales]

    top_categories_labels = [category['variant__product__product_category__category_name'] for category in top_categories]
    top_categories_data = [float(category['total_sold']) for category in top_categories]

    top_brands_labels = [brand['variant__product__product_brand__brand_name'] for brand in top_brands]
    top_brands_data = [float(brand['total_sold']) for brand in top_brands]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_categories': total_categories,
        'monthly_earnings': monthly_earnings,
        'total_sales': total_sales,
        'avg_order_value': round(avg_order_value, 2),
        'latest_orders': latest_orders,
        'best_selling_products': best_selling_products,
        'best_selling_categories': best_selling_categories,
        'best_selling_brands': best_selling_brands,
        'order_status_distribution': order_status_distribution,
        'daily_sales_labels': daily_sales_labels,
        'daily_sales_data': daily_sales_data,
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,
        'yearly_sales_labels': yearly_sales_labels,
        'yearly_sales_data': yearly_sales_data,
        'top_categories_labels': top_categories_labels,
        'top_categories_data': top_categories_data,
        'top_brands_labels': top_brands_labels,
        'top_brands_data': top_brands_data,
    }

    return render(request, 'admin_side/index.html', context)

@login_required(login_url='/admin-panel/login/')
def sales_report(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin-login")
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'daily')
    
    orders = Order.objects.filter(order_status="Delivered")
    
    if start_date and end_date:
        try:
            if report_type == 'daily':
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif report_type == 'monthly':
                start_date = datetime.strptime(start_date, '%Y-%m').date().replace(day=1)
                end_date = (datetime.strptime(end_date, '%Y-%m') + relativedelta(months=1) - timedelta(days=1)).date()
            elif report_type == 'yearly':
                start_date = datetime.strptime(start_date, '%Y').date().replace(month=1, day=1)
                end_date = datetime.strptime(end_date, '%Y').date().replace(month=12, day=31)
            
            # Add one day to end_date to include the end date in the results
            end_date = end_date + timedelta(days=1)
            orders = orders.filter(date__range=[start_date, end_date])
        except ValueError:
            # If date parsing fails, reset the filter
            start_date = None
            end_date = None
    
    if report_type == 'monthly':
        orders = orders.annotate(report_date=TruncMonth('date')).order_by('-report_date', '-date')
    elif report_type == 'yearly':
        orders = orders.annotate(report_date=TruncYear('date')).order_by('-report_date', '-date')
    else:  # daily
        orders = orders.order_by('-date')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Convert back to string for form display
    start_date_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, date) else ''
    end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, date) else ''
    
    # Render the template
    return render(request, 'admin_side/salesreport.html', {
        'page_obj': page_obj,
        'orders': page_obj,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_type': report_type,
    })



