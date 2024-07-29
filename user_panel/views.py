from django.shortcuts import render, get_object_or_404,redirect
from product_management . models import Products, Product_Variant, VariantImage
from django.http import JsonResponse,HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from .models import Address
from category_management.models import Category
from django.db.models import Max
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.contrib import messages
from django.db.models import Q
from product_management .models import Products
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import ProductReview
import re


def variant_images_view(request, variant_id):
    try:
        variant = Product_Variant.objects.get(id=variant_id)
        images = [image.image.url for image in variant.images.all()]
        return JsonResponse({'images': images})
    except Product_Variant.DoesNotExist:
        return JsonResponse({'error': 'Variant not found'}, status=404)
    

@login_required
def add_address(request):

    addresses = Address.objects.filter(user=request.user)
    if request.method == 'POST':
        name = request.POST['name']
        house_name = request.POST['house_name']
        street_name = request.POST['street_name']
        pin_number = request.POST['pin_number']
        district = request.POST['district']
        state = request.POST['state']
        country = request.POST['country']
        phone_number = request.POST['phone_number']
        default = 'default' in request.POST

        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, 'All fields are required.')
            return redirect('user_panel:add-address')
        
        pattern = r'^[A-Za-z][A-Za-z\s]*$'
        
        if not (re.match(pattern, name) and re.match(pattern, house_name) and
            re.match(pattern, street_name) and re.match(pattern, district) and
            re.match(pattern, state) and re.match(pattern, country)):
         messages.error(request, 'Fields should start with a letter and can contain only letters and spaces.')
         return redirect('user_panel:add-address')
        
        if not phone_number.isdigit() or int(phone_number) == 0:
            messages.error(request, 'Phone number must be numeric and cannot be all zeros.')
            return redirect('user_panel:add-address')
        
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
        return redirect('user_panel:add-address')
    return render(request, 'user_side/address_form.html', {'addresses': addresses})


@login_required
def edit_address(request, address_id):

    address = get_object_or_404(Address, id=address_id, user=request.user)

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


        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, 'All fields are required.')
            return redirect('user_panel:add-address')
        
        pattern = r'^[A-Za-z][A-Za-z\s]*$'
        
        if not (re.match(pattern, name) and re.match(pattern, house_name) and
            re.match(pattern, street_name) and re.match(pattern, district) and
            re.match(pattern, state) and re.match(pattern, country)):
         messages.error(request, 'Fields should start with a letter and can contain only letters and spaces.')
         return redirect('user_panel:add-address')
        
        if not phone_number.isdigit() or int(phone_number) == 0:
            messages.error(request, 'Phone number must be numeric and cannot be all zeros.')
            return redirect('user_panel:add-address')


        address.name = name
        address.house_name = house_name
        address.street_name = street_name
        address.pin_number = pin_number
        address.district = district
        address.state = state
        address.country = country
        address.phone_number = phone_number
        address.default = default
                                                                                             
        address.save()
        messages.success(request, 'Address updated successfully.')
        return redirect('user_panel:add-address')

    return render(request, 'user_side/edit_address.html', {'address': address})

def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    address.delete()
    return redirect('user_panel:add-address')



def product_details(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    variants = Product_Variant.objects.filter(product=product).prefetch_related('images')
    selected_variant = variants.first()
    variant_images = selected_variant.images.all() if selected_variant else VariantImage.objects.none()

    # Move selected variant to the beginning of the list
    if selected_variant and selected_variant in variants:
        variants = list(variants)
        variants.remove(selected_variant)
        variants.insert(0, selected_variant)

    # Prepare image URLs for each variant
    for variant in variants:
        variant.image_urls = [image.image.url for image in variant.images.all()]

    related_products = product.related_products()


    context={
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'related_products': related_products,
    }
    return render(request, 'user_side/product_details.html', context)

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment')
    
    review = ProductReview.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        comment=comment
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'review': {
                'rating': review.rating,
                'comment': review.comment,
                'user': review.user.username,
                'created_at': review.created_at.isoformat()
            }
        })
    
    return redirect('user_panel:product-details', product_id=product_id)



@login_required
def shop_list(request):
    products = Products.objects.filter(Q(is_deleted=False) & Q(is_active=True))
    categories = Category.objects.filter(Q(is_deleted=False) & Q(is_available=True))

    sort_by = request.GET.get('sort_by', 'featured')
    query = request.GET.get('query')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    max_product_price = Products.objects.aggregate(Max('offer_price'))['offer_price__max'] or Decimal('0.00')

    # Search filter
    if query:
        products = products.filter(product_name__icontains=query)

    # Category filter
    if category_id:
        products = products.filter(product_category_id=category_id)

    # Price filter
    try:
        if min_price:
            min_price = Decimal(min_price.replace('₹', '').replace(',', ''))
            products = products.filter(offer_price__gte=min_price)
        
        if max_price:
            max_price = Decimal(max_price.replace('₹', '').replace(',', ''))
            products = products.filter(offer_price__lte=max_price)
    except (TypeError, ValueError, ValidationError):
        min_price = None
        max_price = None
        products = Products.objects.none()

    # Sorting
    if sort_by == 'price_low_to_high':
        products = products.order_by('offer_price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-offer_price')
    elif sort_by == 'a_to_z':
        products = products.order_by('product_name')
    elif sort_by == 'z_to_a':
        products = products.order_by('-product_name')

    product_count = products.count()

    context = {
        'products': products,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price if max_price else max_product_price,
        'max_product_price': max_product_price,
        'sort_by': sort_by,
        'query': query,  
        'category_id': category_id, 
        'product_count': product_count,
        
    }

    return render(request, 'user_side/shop_list.html', context)



@login_required
def product_list_by_category(request, category_id=None):
    categories = Category.objects.filter(Q(is_deleted=False) & Q(is_available=True))

    sort_by = request.GET.get('sort_by', 'featured')
    
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id, is_deleted=False)
        products = Products.objects.filter(product_category=selected_category, is_active=True)
    else:
        products = Products.objects.filter(is_active=True)
        selected_category = None

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    max_product_price = Products.objects.aggregate(Max('offer_price'))['offer_price__max'] or Decimal('0.00')

    try:
        if min_price:
            min_price = Decimal(min_price.replace('₹', '').replace(',', ''))
            products = products.filter(offer_price__gte=min_price)
        
        if max_price:
            max_price = Decimal(max_price.replace('₹', '').replace(',', ''))  
            products = products.filter(offer_price__lte=max_price)
    except (TypeError, ValueError, ValidationError):
        min_price = None
        max_price = None
        products = Products.objects.none()

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'min_price': min_price,
        'max_price': max_price if max_price else max_product_price,
        'max_product_price': max_product_price,
        'sort_by': sort_by,
    }

    return render(request, 'user_side/shop_list.html', context)


def user_profile(request):

    return render(request, 'user_side/user_profile.html')


@login_required
def edit_user_profile(request):
    password_form = PasswordChangeForm(user=request.user)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile_form':
            user = request.user
            username = request.POST.get('username', user.username)
            full_name = request.POST.get('full_name', user.full_name)
            email = request.POST.get('email', user.email)
            phone = request.POST.get('phone', user.phone)
            
            if not username or not username[0].isalpha():
                messages.error(request, 'Username must start with an alphabetic character.')
                return redirect('user_panel:edit-user-profile')
            
            if not re.match(r'^[a-zA-Z0-9_]*$', username):
                messages.error(request, 'Username can only contain alphanumeric characters and underscores.')
                return redirect('user_panel:edit-user-profile')
            
            if not full_name or not full_name[0].isalpha():
                messages.error(request, 'Full Name must start with an alphabetic character.')
                return redirect('user_panel:edit-user-profile')
            
            if not re.match(r'^[a-zA-Z0-9_]*$', full_name):
                messages.error(request, 'Full Name can only contain alphanumeric characters and underscores.')
                return redirect('user_panel:edit-user-profile')
            
           
            if phone == '0000000000':  
                messages.error(request, 'Phone number cannot be all zeros.')
                return redirect('user_panel:edit-user-profile')
            
            user.username = username
            user.full_name = full_name
            user.email = email
            user.phone = phone
            user.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_panel:edit-user-profile')
        
        elif form_type == 'password_form':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('user_panel:edit-user-profile')
            else:
                messages.error(request, 'Please correct the error below.')
    
    return render(request, 'user_side/edit_user_profile.html', {'password_form': password_form})
    



