from django.urls import path
from . import views


app_name = 'user_panel'

urlpatterns = [
    
    path('variant-images/<int:variant_id>/', views.variant_images_view, name='variant-images'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
    path('shop-list/', views.shop_list, name='shop-list'),
]
