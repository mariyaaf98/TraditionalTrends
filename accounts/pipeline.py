from accounts.models import User
from social_core.pipeline.partial import partial

@partial
def save_user_details(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')
    user = User.objects.filter(email=email).first()

    if user:
        return {
            'is_new': False,
            'user': user,
        }

    user = User.objects.create_user(
        email=email,
        full_name=details.get('first_name', ''),
        username=details.get('first_name', ''),
        phone=details.get('phone_number', ''), 
    )

    return {
        'is_new': True,
        'user': user,
    }

def activate_user(user, *args, **kwargs):
    user.is_active = True
    user.save()



