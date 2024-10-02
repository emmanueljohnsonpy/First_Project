from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.adminlogin, name='adminlogin'),  
    path('admindashboard', views.admindashboard, name='admindashboard'),
    path('adminproducts', views.adminproducts, name='adminproducts'),
    path('adminaddproduct', views.adminaddproduct, name='adminaddproduct'),
    path('admineditproducts/<int:product_id>/', views.admineditproduct, name='admineditproducts'),
    path('toggle_product_status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('adminusers', views.adminusers, name='adminusers'),
    path('toggle_user_status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('admincategories', views.admincategories, name='admincategories'),
    path('toggle-category-status/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),
    path('adminaddcat', views.adminaddcat, name='adminaddcat'),
    path('admineditcat/<int:category_id>/', views.admineditcat, name='admineditcat'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('order-list', views.order_list, name='order_list'),
    path('change-status/<int:order_id>/', views.change_order_status, name='change_order_status'),
    path('change-status-view/<int:order_id>/', views.change_order_status_view, name='change_order_status_view'),
    path('adminoffers', views.adminoffers, name='adminoffers'),
    path('admincoupons', views.admincoupons, name='admincoupons'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('add-product-offer/', views.add_product_offer, name='add_product_offer'),
    path('add-cat-offer/', views.add_cat_offer, name='add_cat_offer'),
    path('offer/<int:id>/toggle/', views.toggle_offer_status, name='toggle_offer_status'),
    path('edit_offer/<int:id>/', views.edit_offer, name='edit_offer'),
    path('edit-offer/<int:id>/', views.edit_product_offer, name='edit_product_offer'),
    path('edit-cat/<int:id>/', views.edit_cat_offer, name='edit_cat_offer'),
    path('show-items/', views.show_items, name='show_items'),
    path('apply-offer/', views.apply_offer_to_product, name='apply_offer_to_product'),
    path('remove-offer-from-product/', views.remove_offer_from_product, name='remove_offer_from_product'),
    path('apply-offer-to-category/', views.apply_offer_to_category, name='apply_offer_to_category'),
    path('remove-offer-from-category/', views.remove_offer_from_category, name='remove_offer_from_category'),
    path('download-sales-report/', views.generate_pdf, name='download_sales_report'),
    path('download-sales-report-excel/', views.download_sales_report_excel, name='download_sales_report_excel'),
    path('order_detail_view/<int:order_id>/', views.order_detail_view, name='order_detail_view'),
 
]

