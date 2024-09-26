from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'), 
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'), 
    path('resetPassword/', views.resetPassword, name='resetPassword'),
    path('3rdparty/login/cancelled/', views.returntolog, name='returntolog'),

    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('address/', views.address, name='address'),
    path('change_password/', views.change_password, name='change_password'),
    path('ac_details/', views.ac_details, name='ac_details'),
    path('edit_address/<int:id>/', views.edit_address, name='edit_address'),
    path('delete-address-profile/<int:id>/', views.delete_address_profile, name='delete_address_profile'),
    path('wallet/', views.wallet, name='wallet'),

    path('order_detail_view_user/<int:order_id>/', views.order_detail_view_user, name='order_detail_view_user'),
    path('download_pdf/<int:order_id>/', views.generate_pdf, name='download_pdf'),

    path('apply_referral_code/', views.apply_referral_code, name='apply_referral_code'),
]