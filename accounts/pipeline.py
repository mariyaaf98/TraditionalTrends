from accounts.models import User
from social_core.pipeline.partial import partial
from django.db import IntegrityError

@partial
def save_user_details(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')
    if not email:
        return strategy.redirect('error_page')  # Redirect to an error page if email is not provided

    user = User.objects.filter(email=email).first()

    if user:
        return {
            'is_new': False,
            'user': user,
        }

    try:
        # Use the first part of the email as a default username
        default_username = email.split('@')[0]
        
        # Get the full name from details, or use email as a fallback
        full_name = details.get('fullname') or details.get('name') or email
        
        # Set a default phone number if not provided
        phone = details.get('phone') or '0000000000'  # You might want to change this default

        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            username=details.get('username') or default_username,
            phone=phone,
            is_active=True
        )
    except IntegrityError:
        # Handle the case where username might not be unique
        base_username = default_username
        username = base_username
        counter = 1
        while True:
            try:
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    username=username,
                    phone=phone,
                    is_active=True
                )
                break
            except IntegrityError:
                username = f"{base_username}{counter}"
                counter += 1

    return {
        'is_new': True,
        'user': user,
    }