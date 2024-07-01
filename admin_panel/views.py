from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout,authenticate
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import AdminLoginForm
from accounts.models import User

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_index(request):
    return render(request, 'admin_side/index.html')

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
    return redirect('admin_panel:admin_login')

def users_list(request):
    if not request.user.is_superuser:
        return redirect("admin_panel:admin_login")
    user_details = User.objects.all().filter(is_superuser=False)

    return render(request, "admin_side/userslist.html", {"user_details": user_details})

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