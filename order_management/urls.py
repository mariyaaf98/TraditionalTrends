from django.urls import path
from . import views


app_name = 'order_management'

urlpatterns = [
    path('order-success/', views.order_success, name='order-success'),
    path('order-failed/', views.order_failed, name='order-failed'),
    path('order-list/', views.order_list, name='order-list'),
    path('return-order-list/', views.return_order_list, name='return-order-list'),
    path('cancel-order-item/<int:item_id>/', views.cancel_order_item, name='cancel-order-item'),
    path('admin-order-list/', views.admin_order_list, name='admin-order-list'),
    path('admin-order-detail/<int:order_id>', views.admin_order_detail, name='admin-order-detail'),
    path('order-update-status/<int:order_id>/', views.admin_update_order_status, name='order-update-status'),
    path('razorpay-callback/', views.razorpay_callback, name='razorpay-callback'),
    path('wallet/', views.user_wallet_view, name='wallet'),
    path('order-detail/<str:order_id>/', views.user_order_detail, name='order-detail'),
    path('request-return/<int:item_id>/', views.request_return, name='request-return'),
    path('process-return/<int:return_id>/', views.process_return, name='process-return'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    
   
   
]
