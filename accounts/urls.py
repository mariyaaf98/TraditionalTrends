from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

app_name='accounts'

urlpatterns = [
    path('registration/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('', views.home, name='home'),
    path('password-reset/', views.password_reset_request, name='password-reset-request'),
    path('reset/<uidb64>/<token>/', views.password_change_view, name='password_reset_confirm'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
   
   


]
