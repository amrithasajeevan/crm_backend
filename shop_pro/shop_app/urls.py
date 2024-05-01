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
path('coupons/', CouponList.as_view(), name='coupon-list'),
path('coupons/<int:pk>/', CouponDetail.as_view(), name='coupon-detail'),
path('billing-details/', BillingDetailsView.as_view(), name='billing-details'),
path('billing-details/<str:invoice_number>/', BillingDeleteView.as_view(), name='billing-details'),  # Detail view with pk
 path('fetch_google_form_responses/', GoogleFormResponses.as_view(), name='fetch_google_form_responses'),
# path('shopprofit/<int:shop_id>/', ProfitByShopAndDateRangeView.as_view(), name='shop-profit-by-date'),
 path('recommendation-emails/<str:shop_name>/', RecommendationEmails.as_view(), name='recommendation-emails'),
 path('service-form-responses/',service_test.as_view(), name='google_form_responses'),
 path('sevice-verify/',ServiceVerifiedAPIView.as_view(),name='service-verified'),
 path('service-verified/<int:pk>/', ServiceVerifiedDetailAPIView.as_view(), name='service-verified-detail'),
 path('test/',test),
# path('send-offer-emails/', send_offer_emails_view, name='send_offer_emails'),

 path('offers/', OfferAPIView.as_view(), name='offer-list'),
 path('offers/<int:pk>/', OfferDetail.as_view(), name='offer-detail'),
#  path('service-test/',service_test.as_view(),name='test-service'),
 
 path('profitonmonth/<int:shop_id>/',ProfitByShopAndDateView.as_view(),name='profit'),
path('product/<int:product_id>/sentiment/', ProductSentimentAPIView.as_view(), name='product-sentiment'),

]