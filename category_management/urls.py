from django.urls import path
from . import views

app_name = 'category_management'

urlpatterns = [
    path('edit/<int:category_id>/', views.edit_category, name='edit-category'),
    path('delete/<int:category_id>/', views.delete_category, name='delete-category'),
    path('add/', views.add_category, name='add-category'),
    path('category-list/', views.category_list, name='category-list'),
]