from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Products, Product_images
from .models import Category, Brand
from django.core.exceptions import ValidationError
from decimal import Decimal
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import get_object_or_404
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
            # Validate that product_name and price are provided
            if not product_name:
                raise ValidationError("Product name is required.")
            if not price:
                raise ValidationError("Price is required.")
            if len(images) < 3:
                raise ValidationError("At least 3 images are required.")

            # Convert price and offer_price to Decimal
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
    
    images=Product_images.objects.all()
    products = Products.objects.filter(is_deleted=False)
    categories = Products.objects.filter().order_by("id").reverse()

    return render(request, "admin_side/product_list.html", {"categories": categories,'products': products,'images':images})

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