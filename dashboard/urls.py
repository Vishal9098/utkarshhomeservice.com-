from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('orders/', views.orders_list, name='dashboard_orders'),
    path('orders/<str:order_id>/', views.order_detail, name='dashboard_order_detail'),
    path('products/', views.products_list, name='dashboard_products'),
    path('products/add/', views.product_add, name='dashboard_product_add'),
    path('products/edit/<int:pk>/', views.product_edit, name='dashboard_product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='dashboard_product_delete'),
    path('customers/', views.customers_list, name='dashboard_customers'),
    path('categories/', views.categories_list, name='dashboard_categories'),
    path('reviews/', views.reviews_list, name='dashboard_reviews'),
    path('coupons/', views.coupons_list, name='dashboard_coupons'),
    path('coupons/add/', views.coupon_add, name='dashboard_coupon_add'),
    path('analytics/', views.analytics_view, name='dashboard_analytics'),
    path('contacts/', views.contacts_list, name='dashboard_contacts'),
]
