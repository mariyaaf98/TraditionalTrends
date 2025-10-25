import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_otp_email_async(email, otp):
    from_email = os.environ.get("EMAIL_HOST_USER")
    if not from_email:
        print("⚠️ EMAIL_HOST_USER not set in environment variables")
        return

    message = Mail(
        from_email=from_email,
        to_emails=email,
        subject="Your OTP Code",
        html_content=f"<p>Your OTP code is <strong>{otp}</strong>. It will expire in 2 minutes.</p>",
    )

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"✅ OTP sent to {email} (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ SendGrid error: {e}")
