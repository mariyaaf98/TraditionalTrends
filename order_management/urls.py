from django.urls import path
from . import views


app_name = 'order_management'

urlpatterns = [
    path('order-success/', views.order_success, name='order-success'),
    path('order-list/', views.order_list, name='order-list'),
    path('cancel-order-item/<int:item_id>/', views.cancel_order_item, name='cancel-order-item'),
    path('admin-order-list/', views.admin_order_list, name='admin-order-list'),
    path('admin-order-detail/<int:order_id>', views.admin_order_detail, name='admin-order-detail'),
    path('order-update-status/<int:order_id>/', views.admin_update_order_status, name='order-update-status'),

]
