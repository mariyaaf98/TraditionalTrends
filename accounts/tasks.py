import threading
from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp):
    send_mail(
        "Your OTP Code",
        f"Your OTP code is {otp}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

def send_otp_email_async(email, otp):
    thread = threading.Thread(target=send_otp_email, args=(email, otp))
    thread.start()
