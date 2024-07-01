from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Brand
from django.contrib.auth.decorators import login_required

@login_required
def add_brand(request):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        brand_image = request.FILES.get('brand_image')
        status = request.POST.get('status') == 'on'

        # validate all feids
        if not brand_name:
            messages.warning(request, 'Brand Name Cannot Be Empty')
            return redirect('brand_management:add-brand')

        if not brand_image:
            messages.warning(request, 'Brand Image Cannot Be Empty')
            return redirect('brand_management:add-brand')

        if not brand_name.replace(" ", "").isalpha():
            messages.warning(request, 'Brand Name Should Only Contain Alphabetical Characters')
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


def brand_list(request):
    if not request.user.is_superuser:
        return render(request,'admin_panel:admin_login')

    brands=Brand.objects.filter(is_deleted=False).order_by("id")
    return render(request,'admin_side/brand_list.html',{"brands":brands})

def edit_brand(request, brand_id):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')

    brand = get_object_or_404(Brand, pk=brand_id)

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        brand_image = request.FILES.get('brand_image')
        status = request.POST.get('status') == 'on'

        if not brand_name:
            messages.warning(request, 'Brand Name Cannot Be Empty')
            return redirect('brand_management:edit-brand', brand_id=brand_id)
        
        if not brand_name.replace(" ", "").isalpha():
            messages.warning(request, 'Brand Name Should Only Contain Alphabetical Characters')
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
