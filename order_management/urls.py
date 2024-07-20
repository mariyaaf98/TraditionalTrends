from django.urls import path
from . import views


app_name = 'order_management'

urlpatterns = [
    path('order-success/', views.order_success, name='order-success'),
    path('order-list/', views.order_list, name='order-list'),
    path('cancel-order-item/<int:item_id>/', views.cancel_order_item, name='cancel-order-item'),


]
