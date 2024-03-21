from django.urls import path
from .views import *
from . import views

urlpatterns = [


path('register/', AdminRegisterView.as_view(), name='register'),
path('login/', AdminLoginView.as_view(), name='login'),
path('shops/', ShopListCreateAPIView.as_view(), name='shop-list-create'),
path('shops/<int:pk>/', ShopDetailAPIView.as_view(), name='shop-detail'),
path('products/', ProductAddView.as_view(), name='product-list-create'),
path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # GET, PUT, DELETE requests for a specific product
path('employees/', EmployeeAddView.as_view(), name='employee_add'),
path('employees/<int:pk>/', EmployeeAddView.as_view(), name='employee_detail'),
path('stocks/', StockListCreateAPIView.as_view(), name='stock-list-create'),
path('stocks/<int:pk>/', StockDetailAPIView.as_view(), name='stock-detail'),
path('billing-details/', BillingDetailsView.as_view(), name='billing-details'),
path('billing-details/<str:invoice_number>/', BillingDeleteView.as_view(), name='billing-details'),  # Detail view with pk

]