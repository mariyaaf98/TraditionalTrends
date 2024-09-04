from django.core.paginator import Paginator
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import cache_control
from .models import Category
from datetime import date
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.contrib.auth.decorators import login_required

@login_required(login_url='/admin-panel/login/')
def add_category(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    if request.method == "POST":
        category_name = request.POST["category_name"]
        status = request.POST.get("status", False)
        parent = (
            None
            if request.POST["parent"] == "0"
            else Category.objects.get(id=request.POST["parent"])
        )

        # category offer
        try:
            minimum_amount = request.POST.get("minimum_amount", None)
            discount = request.POST.get("discount")or '0'
            discount = Decimal(discount) if discount else None
            expirydate = request.POST.get("date", None)
            if expirydate or minimum_amount:
                expirydate = datetime.strptime(expirydate, "%Y-%m-%d").date()
            else:
                expirydate = None
                minimum_amount = None

        except Exception as e:
            print(e)

        if category_name == "":
            messages.warning(request, "Category Name Cannot Be Empty")
            return redirect("category_management:add-category")

        if not category_name.replace(" ", "").isalpha():
            messages.warning(request, "Category Name Should Only Contain Alphabetical Characters")
            return redirect("category_management:add-category")

        try:
            if Category.objects.filter(category_name=category_name).exists():
                messages.warning(request, "Category Name is Already Taken")
            else:
                Category.objects.create(
                    category_name=category_name,
                    parent=parent,
                    is_available=status,
                    minimum_amount=minimum_amount,
                    discount=discount,
                    expirydate=expirydate,
                )

                messages.success(request, "Category Added Successfully")
                return redirect("category_management:category-list")

        except Exception as e:
            messages.error(request, f"An Error Occurred: {str(e)}")
    
    parentlist = Category.objects.filter(category_name__isnull=False).order_by('id').reverse()
    today = date.today().isoformat()
    return render(request,"admin_side/add_category.html",{"parentlist": parentlist,"today": today})


@login_required(login_url='/admin-panel/login/')
def edit_category(request, category_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    category = get_object_or_404(Category, id=category_id)
    parentlist = Category.objects.filter(parent__isnull=True).exclude(id=category_id)

    if request.method == "POST":
        category_name = request.POST.get("category_name")
        status = request.POST.get("status") == 'on'
        parent = (
            None
            if request.POST.get("parent") == "0"
            else Category.objects.get(id=request.POST["parent"])
        )

        try:
            minimum_amount = request.POST.get("minimum_amount", None)
            discount = request.POST.get("discount") or '0'
            discount = Decimal(discount) if discount else None
            expirydate = request.POST.get("date", None)
            if expirydate or minimum_amount:
                expirydate = datetime.strptime(expirydate, "%Y-%m-%d").date()
            else:
                expirydate = None
                minimum_amount = None

        except Exception as e:
            messages.error(request, f"An Error Occurred: {str(e)}")
            return redirect("category_management:edit-category", category_id=category_id)

        if category_name == "":
            messages.warning(request, "Category Name Cannot Be Empty")
            return redirect("category_management:edit-category", category_id=category_id)

        if not category_name.replace(" ", "").isalpha():
            messages.warning(request, "Category Name Should Only Contain Alphabetical Characters")
            return redirect("category_management:edit-category", category_id=category_id)

        try:
            if Category.objects.filter(category_name=category_name).exclude(id=category_id).exists():
                messages.warning(request, "Category Name is Already Taken")
            else:
                category.category_name = category_name
                category.parent = parent
                category.is_available = status
                category.minimum_amount = minimum_amount
                category.discount = discount
                category.expirydate = expirydate

                category.save()
                messages.success(request, "Category updated successfully")
                return redirect("category_management:category-list")

        except Exception as e:
            messages.error(request, f"An Error Occurred: {str(e)}")
    
    today = date.today().isoformat()
    return render(request, "admin_side/edit_category.html", {"category": category, "parentlist": parentlist, "today": today})


@login_required(login_url='/admin-panel/login/')
def category_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    
    categories_list = Category.objects.all().order_by("-id")
    paginator = Paginator(categories_list, 8) 

    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)

    return render(request, "admin_side/category_list.html", {"categories": categories})


@login_required(login_url='/admin-panel/login/')
def delete_category(request, category_id):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.is_deleted = True
        category.is_available=False
        category.save()
        messages.success(request, "Category deleted successfully")
        return redirect("category_management:category-list")

    return render(request, "admin_side/category_list.html")


@login_required(login_url='/admin-panel/login/')
def restore_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_deleted = False
    category.is_available=True
    category.save()
    return redirect('category_management:category-list')


