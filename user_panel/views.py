from django.shortcuts import render, get_object_or_404,redirect
from product_management . models import Products, Product_Variant, VariantImage
from django.http import JsonResponse,HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from .models import Address
from category_management.models import Category


def variant_images_view(request, variant_id):
    try:
        variant = Product_Variant.objects.get(id=variant_id)
        images = [image.image.url for image in variant.images.all()]
        return JsonResponse({'images': images})
    except Product_Variant.DoesNotExist:
        return JsonResponse({'error': 'Variant not found'}, status=404)
    

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'user_side/address_list.html', {'addresses': addresses})

@login_required
def add_address(request):
    if request.method == 'POST':
        name = request.POST['name']
        house_name = request.POST['house_name']
        street_name = request.POST['street_name']
        pin_number = request.POST['pin_number']
        district = request.POST['district']
        state = request.POST['state']
        country = request.POST['country']
        phone_number = request.POST['phone_number']

        address = Address(
            user=request.user,
            name=name,
            house_name=house_name,
            street_name=street_name,
            pin_number=pin_number,
            district=district,
            state=state,
            country=country,
            phone_number=phone_number
        )
        address.save()
        return redirect('user_panel:address_list')

    return render(request, 'user_side/address_form.html')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.name = request.POST['name']
        address.house_name = request.POST['house_name']
        address.street_name = request.POST['street_name']
        address.pin_number = request.POST['pin_number']
        address.district = request.POST['district']
        address.state = request.POST['state']
        address.country = request.POST['country']
        address.phone_number = request.POST['phone_number']
        address.save()
        return redirect('user_panel:address_list')

    return render(request, 'user_side/address_form.html', {'address': address})

def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    address.delete()
    return JsonResponse({'message': 'Address deleted successfully.'})




def product_details(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    # Fetch variants and their images
    variants = Product_Variant.objects.filter(product=product).prefetch_related('images')
    
    # Determine selected variant (default to first variant)
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

    # Get related products
    related_products = product.related_products()

    return render(request, 'user_side/product_details.html', {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'related_products': related_products,
    })




@login_required
def shop_list(request):
    
    products = Products.objects.filter(is_active=True, is_deleted=False)
    category = Category.objects.filter(is_deleted=False)
    
    context = {
        'products': products,
        'category': category,
    }
    
    return render(request,'user_side/shop_list.html',context)