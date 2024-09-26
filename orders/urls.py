from django.urls import path
from . import views

urlpatterns = [
    path('place_order_two/', views.place_order_two, name='place_order_two'),
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('orders_address/', views.orders_address, name='orders_address'),
    path('update_address/', views.update_address, name='update_address'),
    path('delete_address/<int:id>/', views.delete_address, name='delete_address'),
    path('order-successful/', views.order_successful, name='order_successful'),
    path('create-coupon/', views.create_coupon, name='create_coupon'),
    path('toggle-coupon-status/<int:coupon_id>/', views.toggle_coupon_status, name='toggle_coupon_status'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('retry_page', views.retry_page, name="retry_page"),
    path('check_coupon_status/', views.check_coupon_status, name='check_coupon_status'),
]   
