from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Brand
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDictKeyError

@login_required(login_url='/admin-panel/login/')
def add_brand(request):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        brand_image = request.FILES.get('brand_image')
        status = request.POST.get('status') == 'on'

        # Validate all fields
        if not brand_name:
            messages.warning(request, 'Brand Name Cannot Be Empty')
            return redirect('brand_management:add-brand')

        if not brand_image:
            messages.warning(request, 'Brand Image Cannot Be Empty')
            return redirect('brand_management:add-brand')

        if not brand_name.replace(" ", "").isalpha():
            messages.warning(request, 'Brand Name Should Only Contain Alphabetical Characters')
            return redirect('brand_management:add-brand')

        # Validate image file
        if isinstance(brand_image, UploadedFile):
            if not brand_image.content_type.startswith('image/'):
                messages.warning(request, 'Invalid File Type. Only images are allowed.')
                return redirect('brand_management:add-brand')

        try:
            if Brand.objects.filter(brand_name=brand_name).exists():
                messages.warning(request, 'Brand Name Already Exists')
                return redirect('brand_management:add-brand')
            else:
                Brand.objects.create(brand_name=brand_name, brand_image=brand_image, status=status)
                messages.success(request, 'Brand Added Successfully')
                return redirect('brand_management:brand-list')

        except Exception as e:
            messages.error(request, f"An Error Occurred: {str(e)}")
            return redirect('brand_management:add-brand')

    return render(request, 'admin_side/add_brand.html')


@login_required(login_url='/admin-panel/login/')
def brand_list(request):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')  

    brands = Brand.objects.all().order_by("id")
    
    # Pagination
    paginator = Paginator(brands, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_side/brand_list.html', {"page_obj": page_obj})

@login_required(login_url='/admin-panel/login/')
def edit_brand(request, brand_id):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')

    brand = get_object_or_404(Brand, pk=brand_id)

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        brand_image = request.FILES.get('brand_image')
        status = request.POST.get('status') == 'on'

        # Validate the brand name
        if not brand_name:
            messages.warning(request, 'Brand Name Cannot Be Empty')
            return redirect('brand_management:edit-brand', brand_id=brand_id)
        
        if not brand_name.replace(" ", "").isalpha():
            messages.warning(request, 'Brand Name Should Only Contain Alphabetical Characters')
            return redirect('brand_management:edit-brand', brand_id=brand_id)

        # Validate the image file if provided
        if brand_image:
            if not isinstance(brand_image, UploadedFile) or not brand_image.content_type.startswith('image/'):
                messages.warning(request, 'Invalid File Type. Only images are allowed.')
                return redirect('brand_management:edit-brand', brand_id=brand_id)
        
        try:
            brand.brand_name = brand_name
            if brand_image:
                brand.brand_image = brand_image
            brand.status = status
            brand.save()
            messages.success(request, 'Brand updated successfully.')
            return redirect('brand_management:brand-list')
        except Exception as e:
            messages.error(request, f"An Error Occurred: {str(e)}")
            return redirect('brand_management:edit-brand', brand_id=brand_id)
    else:
        return render(request, 'admin_side/edit_brand.html', {'brand': brand})
    

@login_required(login_url='/admin-panel/login/')
def delete_brand(request, brand_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == "POST":
        brand.is_deleted = True
        brand.save()
        messages.success(request, "Brand deleted successfully")
        return redirect("brand_management:brand-list")

    return render(request, "admin_side/brand_list.html")

def restore_brand(request, brand_id):
    if request.method == 'POST':
       
        brand = get_object_or_404(Brand, id=brand_id, is_deleted=True)
        brand.is_deleted = False
        brand.save()
        messages.success(request, 'Brand restored successfully.')

    return redirect('brand_management:brand-list')