from django.urls import path
from . import views

urlpatterns = [
    path('', views.home,name="index"),
    path('products/', views.products,name="products"),
    path('create_order/',views.create_order,name='create_order'),
    path('razorpay_webhook/',views.razorpay_webhook,name='razorpay_webhook'),
    path('payment_status/<str:order_id>/',views.payment_status,name='payment_status'),
    path('photo/',views.photo,name='home_photo'),
    path('error/',views.error,name='error_page'),
    path('capture-photo/', views.capture_photo, name='capture_photo'),
    path('photobooth_view/<uuid:order_id>/', views.photobooth_view, name='photobooth_view'),
    
]
