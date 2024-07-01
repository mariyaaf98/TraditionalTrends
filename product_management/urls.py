from django.urls import path
from . import views

app_name='product_management'

urlpatterns = [
    path('add-product/', views.add_product, name='add-product'),
    path('product-list/', views.product_list, name='product-list'),
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete-product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit-product'),
]
