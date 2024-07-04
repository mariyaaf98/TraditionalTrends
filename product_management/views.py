from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Products, Product_images, Product_Variant, VariantImage, Category, Brand
from decimal import Decimal
from django.db import transaction

def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_category_id = request.POST.get('product_category')
        product_brand_id = request.POST.get('product_brand')
        price = request.POST.get('price')
        offer_price = request.POST.get('offer_price')
        is_active = request.POST.get('is_active') == 'on'
        thumbnail = request.FILES.get('thumbnail')
        images = request.FILES.getlist('images')

        try:
            if not product_name:
                raise ValidationError("Product name is required.")
            if not price:
                raise ValidationError("Price is required.")
            if len(images) < 3:
                raise ValidationError("At least 3 images are required.")

            price = Decimal(price)
            if offer_price:
                offer_price = Decimal(offer_price)
            else:
                offer_price = None

            category = Category.objects.get(id=product_category_id) if product_category_id else None
            brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

            product = Products.objects.create(
                product_name=product_name,
                product_description=product_description,
                product_category=category,
                product_brand=brand,
                price=price,
                offer_price=offer_price,
                thumbnail=thumbnail,
                is_active=is_active,
            )

            for image in images:
                Product_images.objects.create(product=product, images=image)

            messages.success(request, 'Product added successfully')
            return redirect('product_management:product-list')
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Unexpected error: {str(e)}')

    categories = Category.objects.all()
    brands = Brand.objects.all()

    return render(request, 'admin_side/add_product.html', {'categories': categories, 'brands': brands})

def product_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    images = Product_images.objects.all()
    products = Products.objects.filter(is_deleted=False)
    categories = Products.objects.filter().order_by("id").reverse()

    return render(request, "admin_side/product_list.html", {"categories": categories, 'products': products, 'images': images})

def product_details(request, product_id):
    product = get_object_or_404(Products, pk=product_id)
    product_images = product.product_images_set.all()
    
    context = {
        'product': product,
        'product_images': product_images,
    }
    return render(request, 'admin_side/product_details.html', context)

def delete_product(request, product_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        product.is_deleted = True
        product.save()
        messages.success(request, "Product deleted successfully")
        return redirect("product_management:product-list")

    return redirect("product_management:product-list")

def edit_product(request, product_id):
    products = get_object_or_404(Products, id=product_id)

    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        product_description = request.POST.get("product_description")
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        price = request.POST.get("price")
        offer_price = request.POST.get("offer_price")
        status = request.POST.get("status") == "on"
        thumbnail = request.FILES.get("thumbnail_image")

        if not product_name:
            messages.warning(request, "Product Name Cannot Be Empty")
            return redirect("product_management:edit-product", product_id=product_id)

        if not product_description:
            messages.warning(request, "Product Description Cannot Be Empty")
            return redirect("product_management:edit-product", product_id=product_id)

        if not price:
            messages.warning(request, "Price Cannot Be Empty")
            return redirect("product_management:edit-product", product_id=product_id)

        if not offer_price:
            messages.warning(request, "Offer Price Cannot Be Empty")
            return redirect("product_management:edit-product", product_id=product_id)

        try:
            price = float(price)
            offer_price = float(offer_price)
        except ValueError:
            messages.warning(request, "Please enter valid numeric values for price and offer price")
            return redirect("product_management:edit-product", product_id=product_id)

        if offer_price > price:
            messages.warning(request, "Offer Price Should be less than actual price")
            return redirect("product_management:edit-product", product_id=product_id)

        if price < 0 or offer_price < 0:
            messages.warning(request, "Please enter positive values")
            return redirect("product_management:edit-product", product_id=product_id)

        if not any(char.isalpha() for char in product_name):
            messages.warning(request, "Product Name should contain at least one alphabetical character")
            return redirect("product_management:edit-product", product_id=product_id)

        try:
            brand = get_object_or_404(Brand, id=brand_id)
            category = get_object_or_404(Category, id=category_id)
        except:
            messages.warning(request, "Brand or Category does not exist")
            return redirect("product_management:edit-product", product_id=product_id)

        try:
            with transaction.atomic():
                products.product_name = product_name
                products.product_description = product_description
                products.product_brand = brand
                products.product_category = category
                products.price = price
                products.offer_price = offer_price
                products.is_active = status
                if thumbnail:
                    products.thumbnail = thumbnail
                products.save()

            messages.success(request, "Product Updated Successfully")
            return redirect("product_management:product-list")

        except Exception as e:
            s = f"An Error Occurred: {str(e)}"
            print(s)
            messages.error(request, f"An Error Occurred: {str(e)}")

    content = {
        "products": products,
        "images": Product_images.objects.filter(product=product_id),
        "branddata": Brand.objects.filter(brand_name__isnull=False),
        "categorydata": Category.objects.filter(category_name__isnull=False),
    }

    return render(request, "admin_side/edit-product.html", content)

def add_variant(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    variants = Product_Variant.objects.filter(product=product)
    
    if request.method == 'POST':
        colour_name = request.POST.get('colour_name')
        variant_stock = request.POST.get('variant_stock')
        variant_status = request.POST.get('variant_status') == 'on'
        colour_code = request.POST.get('colour_code')

        # Check if a variant with the same colour_name already exists for the product
        if Product_Variant.objects.filter(product=product, colour_name=colour_name).exists():
            messages.error(request, f"A variant with the colour name '{colour_name}' already exists for this product.")
            return redirect('product_management:add-variant', product_id=product_id)
        
        new_variant = Product_Variant.objects.create(
            product=product,
            colour_name=colour_name,
            variant_stock=variant_stock,
            variant_status=variant_status,
            colour_code=colour_code
        )

        images = request.FILES.getlist('images')
        for image in images:
            VariantImage.objects.create(variant=new_variant, image=image)

        messages.success(request, 'Variant added successfully.')
        return redirect('product_management:variant-list', product_id=product_id)

    return render(request, "admin_side/add_variant.html", {"product": product, 'variants': variants})

def view_variant(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    filter_status = request.GET.get('status', 'all')

    if filter_status == 'active':
        variants = Product_Variant.objects.filter(product=product, is_deleted=False)
    elif filter_status == 'deleted':
        variants = Product_Variant.objects.filter(product=product, is_deleted=True)
    else:
        variants = Product_Variant.objects.filter(product=product)



    return render(request, "admin_side/variant_list.html", {"product": product, 'variants': variants, 'filter_status': filter_status})


def edit_variant(request, variant_id):
    variant = get_object_or_404(Product_Variant, id=variant_id)
    if request.method == 'POST':
        variant.colour_name = request.POST.get('colour_name')
        variant.variant_stock = request.POST.get('variant_stock')
        variant.variant_status = request.POST.get('variant_status') == 'on'
        variant.colour_code = request.POST.get('colour_code')
        
        if 'images' in request.FILES:
            variant.images.all().delete()
            images = request.FILES.getlist('images')
            for image in images:
                VariantImage.objects.create(variant=variant, image=image)
        
        variant.save()
        messages.success(request, 'Variant updated successfully.')
        return redirect('product_management:variant-list', product_id=variant.product.id)
    
    return render(request, 'admin_side/edit-variant.html', {'variant': variant})

def delete_variant(request, variant_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    variant = get_object_or_404(Product_Variant, id=variant_id)

    if request.method == "POST":
        variant.is_deleted = True
        variant.save()
        messages.success(request, "Product variant deleted successfully")
        return redirect("product_management:variant-list", product_id=variant.product.id)

    return redirect("product_management:variant-list", product_id=variant.product.id)



def restore_variant(request, variant_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    variant = get_object_or_404(Product_Variant, id=variant_id)

    if request.method == "POST":
        variant.is_deleted = False
        variant.save()
        messages.success(request, "Product variant restored successfully")
        return redirect("product_management:variant-list", product_id=variant.product.id)

    return redirect("product_management:variant-list", variant_id=variant_id)
