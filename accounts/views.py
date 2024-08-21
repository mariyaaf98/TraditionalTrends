from django.shortcuts import render, redirect,get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
import random
from product_management.models import Products,Product_images
from category_management.models import Category
from brand_management.models import Brand
from .forms import RegisterForm, LoginForm,PasswordResetRequestForm,CustomPasswordChangeForm
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from cart_management.models import Cart, CartItem
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash

# Generate a random OTP
def generate_otp():
    return random.randint(100000, 999999)


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Store user ID in the session
                    request.session['user_id'] = user.id

                    return redirect('accounts:home')
                else:
                    form.add_error(None, 'This account is blocked.')
                    messages.error(request, 'This account is blocked.')
            else:
                form.add_error(None, 'Invalid email or password')
                messages.error(request, 'Invalid email or password')
    else:
        form = LoginForm()
    
    return render(request, 'user_side/accounts/login.html', {'form': form})



def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 

            otp = generate_otp()
            send_mail(
                "Your OTP Code",
                f"Your OTP code is {otp}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            # Store the OTP in the session
            request.session['otp'] = str(otp)
            request.session['user_data'] = form.cleaned_data
            request.session['otp_creation_time'] = timezone.now().isoformat()
            return redirect('accounts:verify_otp')
    else:
        form = RegisterForm()
    return render(request, 'user_side/accounts/register.html', {'form': form})



def verify_otp(request):
    otp_creation_time = request.session.get('otp_creation_time')
    
    if not otp_creation_time:
        messages.error(request, 'OTP not found or expired. Please try registering again.')
        return redirect('accounts:user_register')
    
    otp_creation_time = parse(otp_creation_time)
    otp_expiration_time = otp_creation_time + timezone.timedelta(seconds=120)

    if request.method == "POST":
        entered_otp = request.POST.get('entered_otp')
        otp = request.session.get('otp')
        user_data = request.session.get('user_data')

        #if the OTP or OTP creation time is not found in the session
        if not otp or not otp_creation_time:  
            messages.error(request, 'OTP not found or expired. Please try registering again.')
            return redirect('accounts:user_register')

        if (timezone.now() - otp_creation_time).total_seconds() > 120:
            messages.error(request, 'OTP expired. Please try registering again.')
            return redirect('accounts:user_register')

        if entered_otp == otp:
            user = User.objects.create_user(
                full_name=user_data['full_name'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                phone=user_data['phone'],
            )
            user.is_active = True
            user.save()

            backend = 'accounts.backends.EmailBackend'
            user.backend = backend
            login(request, user, backend=backend)

            # Clear session data
            request.session.pop('otp', None)
            request.session.pop('otp_creation_time', None)
            request.session.pop('user_data', None)
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid OTP')
    
    return render(request, 'user_side/accounts/otp_verify.html', {'otp_expiration_time': otp_expiration_time.isoformat()})


def resend_otp(request):
    user_data = request.session.get('user_data')

    if not user_data:
        messages.error(request, 'User data not found. Please try registering again.')
        return redirect('accounts:user_register')

    otp = generate_otp()
    send_mail(
        "Your OTP Code",
        f"Your new OTP code is {otp}",
        settings.DEFAULT_FROM_EMAIL,
        [user_data['email']],
    )

    request.session['otp'] = str(otp)
    request.session['otp_creation_time'] = timezone.now().isoformat()

    messages.success(request, 'A new OTP has been sent to your email.')
    return redirect('accounts:verify_otp')


def home(request):
    products = Products.objects.filter(is_active=True, is_deleted=False)
    category = Category.objects.filter(is_deleted=False)

    
    cart = None
    cart_items = []
    total_price = 0

    # Check if the user is authenticated
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.variant.product.offer_price * item.quantity for item in cart_items)

    context = {
        'products': products,
        'category': category,
        'total_price': total_price,
        'cart_items': cart_items,
    }
    
    return render(request, 'user_side/index.html', context)
    
    
@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:home')



def password_reset_request(request):
    if 'email' in request.GET:
        email = request.GET['email']
        user = User.objects.filter(email=email).first()
        
        if user:
            # User exists, send reset email
            subject = "Password Reset Requested"
            email_template_name = "user_side/accounts/password_reset_email.html"
            context = {
                "email": user.email,
                "domain": get_current_site(request).domain,
                "site_name": "Your Site Name",
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": default_token_generator.make_token(user),
                "protocol": "https" if request.is_secure() else "http",
            }
            email_body = render_to_string(email_template_name, context)
            send_mail(subject, email_body, "noreply@yourdomain.com", [user.email], fail_silently=False)
            messages.success(request, "A link to reset your password has been sent to your email.")
        else:
            # User does not exist
            messages.error(request, "No registered user found with this email address.")
    else:
        messages.error(request, "Email address is required.")
    
    return redirect("accounts:user_login")



def generate_password_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    return reset_link


def password_change_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomPasswordChangeForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Your password has been reset successfully. You can now log in.')
                return redirect('accounts:user_login')
        else:
            form = CustomPasswordChangeForm()

        return render(request, 'user_side/accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The reset link is invalid or has expired.')
        return redirect('accounts:password_reset_request')


def password_reset_done(request):
    messages.success(request, "Your password has been reset successfully. You can now log in with your new password.")
    return redirect('accounts:user_login')
