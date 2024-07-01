from django.urls import path
from . import views

app_name='admin_panel'

urlpatterns = [
    path('login/', views.admin_login, name='admin-login'),
    path('admin-index/', views.admin_index, name='admin-index'),
    path('userlist/', views.users_list, name='users-list'),
    path('block-unblock/<int:id>/', views.block_unblock_user, name='block-unblock'),

]
