from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.all_services, name='all_services'),
    path('service/<slug:slug>/', views.service_detail, name='service_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:service_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/', views.checkout, name='checkout'),
    path('service/book/<int:service_id>/', views.book_now, name='book_now'),  # ✅ NEW
    path('order/success/<str:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('contact/', views.contact, name='contact'),
    path('review/add/<int:service_id>/', views.add_review, name='add_review'),
    path('search/', views.search, name='search'),
    path('order/<str:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    # path('invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('dashboard/', views.dashboard, name='dashboard'),
   
]