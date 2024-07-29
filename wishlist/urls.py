from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/<int:wishlist_item_id>/', views.remove_from_wishlist, name='remove-from-wishlist'),
    path('view-wishlist/', views.view_wishlist, name='view-wishlist'),
]
