from django.urls import path
from . import views


app_name = 'coupon_management'

urlpatterns = [
    path('create-coupon/', views.create_coupon, name='create_coupon'),
    path('coupon-list/', views.coupon_list, name='coupon-list'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit-coupon'),
    path('delete-coupon/<int:coupon_id>/', views.delete_coupon, name='delete-coupon'),
    path('apply-coupon/', views.apply_coupon, name='apply-coupon'),
    # path('available-coupons/', views.available_coupons, name='available-coupons'),
   path('remove-coupon/', views.remove_coupon, name='remove-coupon'),
    
]
