from django.urls import path
from . import views

app_name = 'brand_management'

urlpatterns = [
    
    path('add-brand/', views.add_brand, name='add-brand'),
    path('brand-list/', views.brand_list, name='brand-list'),
    path('edit-brand/<int:brand_id>/', views.edit_brand, name='edit-brand'),
    path('delete-brand/<int:brand_id>/', views.delete_brand, name='delete-brand'),
    path('brand/restore/<int:brand_id>/', views.restore_brand, name='restore-brand'),
]
