from django.urls import path
from . import views


app_name = 'user_panel'

urlpatterns = [
    
    path('variant-images/<int:variant_id>/', views.variant_images_view, name='variant-images'),
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
    path('shop-list/', views.shop_list, name='shop-list'),
    path('shop-list/category/<int:category_id>/', views.product_list_by_category, name='product-list-by-category'),
    path('add-address/',views.add_address,name='add-address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit-address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete-address'),
    path('profile/',views.user_profile,name='user-profile'),
    path('edit-user-profile/', views.edit_user_profile, name='edit-user-profile'),
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),
   




]
