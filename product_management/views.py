from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Products, Product_images, Product_Variant, VariantImage, Category, Brand
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponseRedirect
from django.core.paginator import Paginator

# @login_required
# def add_product(request):
#     if not request.user.is_superuser:
#         return redirect("admin_panel:admin_login")
    
#     if request.method == 'POST':
#         product_name = request.POST.get('product_name')
#         product_description = request.POST.get('product_description')
#         product_category_id = request.POST.get('product_category')
#         product_brand_id = request.POST.get('product_brand')
#         price = request.POST.get('price')
#         use_percentage = request.POST.get('use_percentage') == 'on'
#         offer_price = request.POST.get('offer_price')
#         offer_percentage = request.POST.get('offer_percentage')
#         is_active = request.POST.get('is_active') == 'on'
#         thumbnail = request.FILES.get('thumbnail')
#         images = request.FILES.getlist('images')

#         try:
#             if not product_name:
#                 raise ValidationError("Product name is required.")
#             if not price:
#                 raise ValidationError("Price is required.")
           
#             price = Decimal(price)
            
#             if use_percentage:
#                 if not offer_percentage:
#                     raise ValidationError("Offer percentage is required when using percentage.")
#                 offer_percentage = Decimal(offer_percentage)
#                 if offer_percentage < 1 or offer_percentage > 70:
#                     raise ValidationError("Offer percentage must be between 1 and 70.")
#                 offer_price = price * (1 - offer_percentage / 100)
#             elif offer_price:
#                 offer_price = Decimal(offer_price)
#             else:
#                 offer_price = None

#             if offer_price is not None:
#                 if offer_price < 0:
#                     messages.warning(request, "Offer price cannot be negative.")
#                     return redirect('product_management:add-product')
#                 if offer_price >= price:
#                     messages.warning(request, "Offer Price should be less than the actual price.")
#                     return redirect('product_management:add-product')
            
             
#             if thumbnail:
#                 if not thumbnail.content_type.startswith('image/'):
#                     messages.warning(request, "Invalid file type for thumbnail. Only image files are allowed.")
#                     return redirect('product_management:add-product')
            
            
#             for image in images:
#                 if not image.content_type.startswith('image/'):
#                     messages.warning(request, "Invalid file type in images. Only image files are allowed.")
#                     return redirect('product_management:add-product')
            
#             category = Category.objects.get(id=product_category_id) if product_category_id else None
#             brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

#             product = Products.objects.create(
#                 product_name=product_name,
#                 product_description=product_description,
#                 product_category=category,
#                 product_brand=brand,
#                 price=price,
#                 offer_price=offer_price,
#                 thumbnail=thumbnail,
#                 is_active=is_active,
#             )

#             for image in images:
#                 Product_images.objects.create(product=product, images=image)

#             messages.success(request, 'Product added successfully')
#             return redirect('product_management:product-list')
        
#         except ValidationError as e:
#             messages.error(request, f'Validation error: {str(e)}')
        
#         except Exception as e:
#             messages.error(request, f'Unexpected error: {str(e)}')

#     categories = Category.objects.all()
#     brands = Brand.objects.all()

#     return render(request, 'admin_side/add_product.html', {'categories': categories, 'brands': brands})


@login_required
def add_product(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_category_id = request.POST.get('product_category')
        product_brand_id = request.POST.get('product_brand')
        price = request.POST.get('price')
        use_percentage = request.POST.get('use_percentage') == 'on'
        offer_price = request.POST.get('offer_price')
        offer_percentage = request.POST.get('offer_percentage')
        is_active = request.POST.get('is_active') == 'on'
        thumbnail = request.FILES.get('thumbnail')
        images = request.FILES.getlist('images')

        try:
            if not product_name:
                raise ValidationError("Product name is required.")
            if not price:
                raise ValidationError("Price is required.")
           
            price = Decimal(price)
            
            # If 'use_percentage' is checked, calculate 'offer_price' using 'offer_percentage'
            if use_percentage:
                if not offer_percentage:
                    raise ValidationError("Offer percentage is required when using percentage.")
                offer_percentage = Decimal(offer_percentage)
                if offer_percentage < 1 or offer_percentage > 70:
                    raise ValidationError("Offer percentage must be between 1 and 70.")
                offer_price = price * (1 - offer_percentage / 100)
            
            # If 'offer_price' is provided, validate it
            elif offer_price:
                offer_price = Decimal(offer_price)

                # Ensure that the 'offer_price' is less than the actual 'price'
                if offer_price >= price:
                    raise ValidationError("Offer Price should be less than the actual price.")
            else:
                # If 'offer_price' is empty, set it equal to 'price'
                offer_price = price

            # Check if 'offer_price' is valid (if not already caught in the earlier checks)
            if offer_price is not None and offer_price < 0:
                messages.warning(request, "Offer price cannot be negative.")
                return redirect('product_management:add-product')
            
            if thumbnail:
                if not thumbnail.content_type.startswith('image/'):
                    messages.warning(request, "Invalid file type for thumbnail. Only image files are allowed.")
                    return redirect('product_management:add-product')
            
            for image in images:
                if not image.content_type.startswith('image/'):
                    messages.warning(request, "Invalid file type in images. Only image files are allowed.")
                    return redirect('product_management:add-product')
            
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



@login_required
def product_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    products = Products.objects.all()
    paginator = Paginator(products, 10)  # Show 10 products per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Products.objects.filter().order_by("id").reverse()
    images = Product_images.objects.all()

    return render(request, "admin_side/product_list.html", {
        "categories": categories,
        'page_obj': page_obj,
        'images': images
    })


@login_required
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

@login_required
def restore_product(request, product_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        product.is_deleted = False
        product.save()
        messages.success(request, "Product restored successfully")
        return redirect("product_management:product-list")

    return redirect("product_management:product-list")

# @login_required
# def edit_product(request, product_id):
#     print('jhasdbgkljhdsg')
#     if not request.user.is_superuser:
#         return redirect("admin_panel:admin_login")

#     products = get_object_or_404(Products, id=product_id)

#     if request.method == "POST":
#         product_name = request.POST.get("product_name")
#         product_description = request.POST.get("product_description")
#         brand_id = request.POST.get("brand")
#         category_id = request.POST.get("category")
#         price = request.POST.get("price")
#         use_percentage = request.POST.get("use_percentage") == "on"
#         offer_price = request.POST.get("offer_price")
#         offer_percentage = request.POST.get("offer_percentage")
#         status = request.POST.get("status") == "on"
#         thumbnail = request.FILES.get("thumbnail_image")

#         # Check if required fields are missing
#         if not product_name:
#             messages.error(request, "Product Name cannot be empty")
#         if not product_description:
#             messages.error(request, "Product Description cannot be empty")
#         if not price:
#             messages.error(request, "Price cannot be empty")

#         # If any of the fields are empty, redirect back to the edit page
#         if not product_name or not product_description or not price:
#             return redirect("product_management:edit-product", product_id=product_id)

#         try:
#             price = float(price)
#             if price < 0:
#                 raise ValueError("Price must be positive")

#             if use_percentage:
#                 if not offer_percentage:
#                     messages.warning(request, "Offer Percentage cannot be empty when using percentage")
#                     return redirect("product_management:edit-product", product_id=product_id)
#                 offer_percentage = float(offer_percentage)
#                 if offer_percentage < 1 or offer_percentage > 70:
#                     raise ValueError("Offer Percentage must be between 1 and 70")
#                 offer_price = price * (1 - offer_percentage / 100)
#             else:
#                 if not offer_price:
#                     messages.warning(request, "Offer Price cannot be empty when not using percentage")
#                     return redirect("product_management:edit-product", product_id=product_id)
#                 offer_price = float(offer_price)
#                 if offer_price < 0:
#                     raise ValueError("Offer Price must be positive")
#                 if offer_price >= price:
#                     messages.warning(request, "Offer Price should be less than the actual price")
#                     return redirect("product_management:edit-product", product_id=product_id)

#         except ValueError as e:
#             messages.warning(request, str(e))
#             return redirect("product_management:edit-product", product_id=product_id)

#         if not any(char.isalpha() for char in product_name):
#             messages.warning(request, "Product Name should contain at least one alphabetical character")
#             return redirect("product_management:edit-product", product_id=product_id)

#         try:
#             brand = get_object_or_404(Brand, id=brand_id)
#             category = get_object_or_404(Category, id=category_id)
#         except:
#             messages.warning(request, "Brand or Category does not exist")
#             return redirect("product_management:edit-product", product_id=product_id)

#         try:
#             with transaction.atomic():
#                 products.product_name = product_name
#                 products.product_description = product_description
#                 products.product_brand = brand
#                 products.product_category = category
#                 products.price = price
#                 products.offer_price = offer_price
#                 products.is_active = status
#                 if thumbnail:
#                     products.thumbnail = thumbnail
#                 products.save()

#             messages.success(request, "Product Updated Successfully")
#             return redirect("product_management:product-list")

#         except Exception as e:
#             print(f"An Error Occurred: {str(e)}")
#             messages.error(request, f"An Error Occurred: {str(e)}")

#     content = {
#         "products": products,
#         "images": Product_images.objects.filter(product=product_id),
#         "branddata": Brand.objects.filter(brand_name__isnull=False),
#         "categorydata": Category.objects.filter(category_name__isnull=False),
#     }

#     return render(request, "admin_side/edit-product.html", content)


@login_required
def edit_product(request, product_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    products = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        product_description = request.POST.get("product_description")
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        price = request.POST.get("price")
        use_percentage = request.POST.get("use_percentage") == "on"
        offer_price = request.POST.get("offer_price")
        offer_percentage = request.POST.get("offer_percentage")
        status = request.POST.get("status") == "on"
        thumbnail = request.FILES.get("thumbnail_image")

        # Check if required fields are missing
        if not product_name:
            messages.error(request, "Product Name cannot be empty")
        if not product_description:
            messages.error(request, "Product Description cannot be empty")
        if not price:
            messages.error(request, "Price cannot be empty")

        # If any of the fields are empty, redirect back to the edit page
        if not product_name or not product_description or not price:
            return redirect("product_management:edit-product", product_id=product_id)

        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be positive")

            if use_percentage:
                if not offer_percentage:
                    messages.warning(request, "Offer Percentage cannot be empty when using percentage")
                    return redirect("product_management:edit-product", product_id=product_id)
                offer_percentage = float(offer_percentage)
                if offer_percentage < 1 or offer_percentage > 70:
                    raise ValueError("Offer Percentage must be between 1 and 70")
                offer_price = price * (1 - offer_percentage / 100)
            else:
                if offer_price:
                    offer_price = float(offer_price)
                    if offer_price < 0:
                        raise ValueError("Offer Price must be positive")
                    if offer_price >= price:
                        messages.warning(request, "Offer Price should be less than the actual price")
                        return redirect("product_management:edit-product", product_id=product_id)
                else:
                    # If offer price is not set, default it to the regular price
                    offer_price = price

        except ValueError as e:
            messages.warning(request, str(e))
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
            print(f"An Error Occurred: {str(e)}")
            messages.error(request, f"An Error Occurred: {str(e)}")

    content = {
        "products": products,
        "images": Product_images.objects.filter(product=product_id),
        "branddata": Brand.objects.filter(brand_name__isnull=False),
        "categorydata": Category.objects.filter(category_name__isnull=False),
    }

    return render(request, "admin_side/edit-product.html", content)


@login_required
def add_variant(request, product_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
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

        # Process uploaded images
        images = request.FILES.getlist('product_images')
        for image in images:
            VariantImage.objects.create(variant=new_variant, image=image)

        messages.success(request, 'Variant added successfully.')
        return redirect('product_management:variant-list', product_id=product_id)

    return render(request, "admin_side/add_variant.html", {"product": product, 'variants': variants})



@login_required
def view_variant(request, product_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    product = get_object_or_404(Products, id=product_id)
    filter_status = request.GET.get('status', 'all')

    if filter_status == 'active':
        variants = Product_Variant.objects.filter(product=product, is_deleted=False).prefetch_related('images')
    elif filter_status == 'deleted':
        variants = Product_Variant.objects.filter(product=product, is_deleted=True).prefetch_related('images')
    else:
        variants = Product_Variant.objects.filter(product=product).prefetch_related('images')

    context = {
        "product": product,
        'variants': variants,
        'filter_status': filter_status
    }

    return render(request, "admin_side/variant_list.html", context)



@login_required
def edit_variant(request, variant_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    variant = get_object_or_404(Product_Variant, id=variant_id)
    
    if request.method == 'POST':
        variant.colour_name = request.POST.get('colour_name')
        variant.variant_stock = request.POST.get('variant_stock')
        variant.variant_status = request.POST.get('variant_status') == 'on'
        variant.colour_code = request.POST.get('colour_code')
        variant.save()
        
        images = request.FILES.getlist('images')
        for image in images:
            VariantImage.objects.create(variant=variant, image=image)
        
        messages.success(request, 'Variant updated successfully.')
        return redirect('product_management:variant-list', product_id=variant.product.id)

    return render(request, 'admin_side/edit-variant.html', {"variant": variant})



@login_required
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



@login_required
def delete_variant_image(request, image_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    image = get_object_or_404(VariantImage, id=image_id)
    variant_id = image.variant.id
    image.delete()
    messages.success(request, 'Image deleted successfully.')
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
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


