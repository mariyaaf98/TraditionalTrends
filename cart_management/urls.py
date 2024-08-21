
from django.urls import path
from . import views


app_name = 'cart_management'

urlpatterns = [
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('cart-view/', views.cart_view, name='cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('delete-cart-item/<int:item_id>/', views.delete_cart_item, name='delete-cart-item'),
    path('cart/clear/', views.clear_cart, name='clear-cart'),
    path('update-default-address/', views.update_default_address, name='update_default_address'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-add-address/',views.checkout_add_address,name='checkout-add-address'),
    path('update-counts/', views.update_counts, name='update-counts'),
]

