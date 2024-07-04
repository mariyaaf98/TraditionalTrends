from django.urls import path
from . import views

app_name='product_management'

urlpatterns = [
    path('add-product/', views.add_product, name='add-product'),
    path('product-list/', views.product_list, name='product-list'),
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete-product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit-product'),
    path('add-variant/<int:product_id>/', views.add_variant, name='add-variant'),
    path('variant-list/<int:product_id>/', views.view_variant, name='variant-list'),
    path('edit-variant/<int:variant_id>/', views.edit_variant, name='edit-variant'),
    path('delete-variant/<int:variant_id>/', views.delete_variant, name='delete-variant'),
    path('restore-variant/<int:variant_id>/', views.restore_variant, name='restore-variant'),

]
