from django.urls import path
from . import views 

app_name='accounts'

urlpatterns = [
    path('', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('home/', views.home, name='home'),
]
