from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from .models import Shop
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from rest_framework import generics, status
from .serializers import *
from .serializers import CustomUserSerializer, loginserializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class AdminRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "Registered successfully", 'data': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        qs = User.objects.all()
        serializer = CustomUserSerializer(qs, many=True)
        return Response(serializer.data)

class AdminLoginView(APIView):
    def post(self, request):
        serializer = loginserializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")
            
            user = authenticate(request, username=username, password=password)
            
            if user:
                login(request, user)
                data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                
            }
                # Generate or retrieve the token for the user
                token, created = Token.objects.get_or_create(user=user)
                return Response({'msg': 'logged in successfully','data':data, 'token': token.key})
            else:
                return Response({'msg': 'login failed'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ShopListCreateAPIView(APIView):
    def get(self, request):
        shops = Shop.objects.all()
        serializer = ShopSerializer(shops, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShopDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Shop.objects.get(pk=pk)
        except Shop.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        shop = self.get_object(pk)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def put(self, request, pk):
        shop = self.get_object(pk)
        serializer = ShopSerializer(shop, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        shop = self.get_object(pk)
        shop.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

import requests
from bs4 import BeautifulSoup
import csv
import time
from concurrent.futures import ThreadPoolExecutor
from textblob import TextBlob
from rest_framework import status
from rest_framework import status as http_status
from django.core.files import File
import os


class ProductAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            shop_name = request.data.get('shop_name', None)
            if shop_name:
                try:
                    shop = Shop.objects.get(shop_name=shop_name, user=request.user)
                except Shop.DoesNotExist:
                    print("Shop not found for shop_name:", shop_name, "and user:", request.user)
                    return Response({'error': 'Shop not found or not associated with the user'}, status=http_status.HTTP_404_NOT_FOUND)
                pro_company = request.data.get('pro_company', None)
                product_name = request.data.get('product_name', None)
                if pro_company and product_name :
                    try:
                        stock = Stock.objects.get(pro_company=pro_company, productname=product_name)
                    except Stock.DoesNotExist:
                        return Response({'error': 'Stock not found for the given pro_company and productname'}, status=http_status.HTTP_404_NOT_FOUND)

                    # Update the serializer data with the correct stock instance
                    serializer.validated_data['stock'] = stock
                    serializer.validated_data['stock_quantity'] = stock.quantity

                    # Assuming the serializer.save() will automatically associate the shop and other fields
                    product = serializer.save(shop=shop)
                    # Get serialized product data
                    product_data = serializer.data
                    sentiments = product.count_sentiments()
                    product_data['sentiments'] = sentiments

                    return Response({'message': 'Product successfully added','data':product_data}, status=http_status.HTTP_201_CREATED)
                else:
                    return Response({'error': 'pro_company, productname, and product_link are required'}, status=http_status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Shop name is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        products = Product.objects.all()
        serialized_products = []
        for product in products:
            serialized_product = ProductSerializer(product).data
            sentiments = product.count_sentiments()
            serialized_product['sentiments'] = sentiments 
            serialized_products.append(serialized_product)
        return Response({'products': serialized_products}, status=http_status.HTTP_200_OK)

 

from rest_framework.exceptions import PermissionDenied
from django.http import Http404

class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self, product_id):
        try:
            # Explicitly select the related Shop object
            product = Product.objects.select_related('shop').get(pk=product_id)
            # Access the users associated with the shop (assuming it's a ManyToMany relationship)
            shop_users = product.shop.user.all()

            # Now you need to check if the requesting user is in the list of shop_users
            if self.request.user not in shop_users:
                raise PermissionDenied("You are not authorized to perform this action")

            return product
        except Product.DoesNotExist:
            raise Http404("Product not found")

    def get(self, request, product_id):
        product = self.get_object(product_id)
        serializer = ProductSerializer(product)
        sentimental_count = product.count_sentiments()  # Retrieve sentimental count
        response_data = serializer.data
        response_data['stock_quantity'] = product.stock_quantity
        response_data['sentimental_count'] = sentimental_count  # Add sentimental count to response data
        return Response({'message': 'Product retrieved successfully', 'data': response_data}, status=status.HTTP_200_OK)

    def put(self, request, product_id):
        product = self.get_object(product_id)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Product updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        product = self.get_object(product_id)
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        


class EmployeeAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            # Ensure that only the shop associated with the employee can add them
            if request.user.shop.id == serializer.validated_data['shop'].id:
                serializer.save()
                return Response({'message': 'Employee successfully added'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'You are not authorized to add employees for this shop'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def get(self, request):
        employee = Employee.objects.all()
        serializer = EmployeeSerializer(employee,many=True)
        return Response(serializer.data)
    

    def put(self, request, pk):
        employee = self.get_object(pk)
        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            # Ensure that only the shop associated with the employee can update them
            if request.user.shop.id == serializer.validated_data['shop'].id:
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({'error': 'You are not authorized to update employees for this shop'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        employee = self.get_object(pk)
        # Ensure that only the shop associated with the employee can delete them
        if request.user.shop.id == employee.shop.id:
            employee.delete()
            return Response({'message': 'Employee successfully deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'You are not authorized to delete employees for this shop'}, status=status.HTTP_403_FORBIDDEN)
        



class StockListCreateAPIView(APIView):
    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StockSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Stock created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Stock.objects.get(pk=pk)
        except Stock.DoesNotExist:
            return None

    def get(self, request, pk):
        stock = self.get_object(pk)
        if stock:
            serializer = StockSerializer(stock)
            return Response(serializer.data)
        return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        stock = self.get_object(pk)
        if stock:
            serializer = StockSerializer(stock, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Stock updated successfully'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        stock = self.get_object(pk)
        if stock:
            stock.delete()
            return Response({'message': 'Stock deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
    

class CouponList(APIView):
    def get(self, request):
        coupons = Coupon.objects.all()
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CouponDetail(APIView):
    def get_object(self, pk):
        try:
            return Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        coupon = self.get_object(pk)
        serializer = CouponSerializer(coupon)
        return Response(serializer.data)

    def put(self, request, pk):
        coupon = self.get_object(pk)
        serializer = CouponSerializer(coupon, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        coupon = self.get_object(pk)
        coupon.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

from django.db.models import Sum  # Import Sum function from Django
import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Sum  # Import Sum function from Django
from rest_framework import permissions

class IsShopOwner(permissions.BasePermission):
    """
    Custom permission to only allow shop owners to add billing details.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and associated with any shop as its owner
        return request.user.is_authenticated and request.user.shop_set.exists()
    
from rest_framework import permissions
from django.utils import timezone


class IsShopOwner(permissions.BasePermission):
    """
    Custom permission to only allow shop owners to add billing details.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and associated with any shop as its owner
        return request.user.is_authenticated and request.user.shop_set.exists()

class BillingDetailsView(APIView):
    permission_classes = [IsAuthenticated, IsShopOwner]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            # Extract relevant information from the request data
            shop_name = request.data.get('shop_name')
            customer_name = request.data.get('customer_name')
            phone_number = request.data.get('phone_number')
            email = request.data.get('email')
            invoice_number = request.data.get('invoice_number')
            coupon_code = request.data.get('coupon_code')
            payment_status = request.data.get('payment_status')
            payment_method = request.data.get('payment_method')
            products_data = request.data.get('products')
            
            # Get the shop associated with the authenticated user and specified shop name
            shop = request.user.shop_set.filter(shop_name=shop_name).first()
            if not shop:
                return Response({'error': f'Shop "{shop_name}" does not belong to the authenticated user.'}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize variables to store total amount and billing details list
            total_amount = 0
            billing_details_list = []

            for product_data in products_data:
                product_name = product_data['product_name']
                quantity = product_data['quantity']

                # Check if the product belongs to the specified shop
                if not Product.objects.filter(product_name=product_name, shop=shop).exists():
                    return Response({'error': f'Product "{product_name}" does not belong to shop "{shop_name}".'}, status=status.HTTP_400_BAD_REQUEST)

                # Retrieve the product based on the provided product_name
                product = Product.objects.get(product_name=product_name, shop=shop)

                # Check if stock is available for the product
                stock_item = Stock.objects.get(productname=product_name)
                if stock_item.quantity < quantity:
                    return Response({'error': f'Insufficient stock for {product_name}'}, status=status.HTTP_400_BAD_REQUEST)

                # Calculate the total amount for this item
                item_total_amount = product.selling_price * quantity

                # Update the running total with the current item's total amount
                total_amount += item_total_amount

                # Create billing details for each product
                billing_details = BillingDetails(
                    shop=shop,
                    customer_name=customer_name,
                    phone_number=phone_number,
                    email=email,
                    invoice_number=invoice_number,
                    product_name=product_name,
                    price=product.selling_price,
                    quantity=quantity,
                    total_amount=item_total_amount,  # Use the total amount for this item
                    coupon_code=coupon_code,
                    payment_status=payment_status,
                    payment_method=payment_method,
                    billing_date=timezone.now().date(),
                    invoice_date=timezone.now().date(),
                )
                billing_details.save()

                # Append billing details to the list
                billing_details_list.append({
                    'id': billing_details.id,
                    'shop_name': shop_name,
                    'product_name': billing_details.product_name,
                    'price': billing_details.price,
                    'quantity': billing_details.quantity,
                    'total_amount': billing_details.total_amount
                })

                # Update stock quantity
                stock_item.quantity -= quantity
                stock_item.save()

            # Apply coupon code discount if available
            coupon_discount = 0  # Default discount is 0
            if coupon_code:
                coupon = Coupon.objects.filter(coupon_code=coupon_code).first()
                if coupon:
                    coupon_discount = coupon.amount

            # Subtract coupon code discount from the total amount
            total_amount -= coupon_discount

            # Return response with total amount and billing details list
            response_data = {
                'message': 'Billing details saved successfully.',
                'total_amount': total_amount,
                'billing_details': billing_details_list,
                'grand_total': total_amount,  # Return the total amount as grand total
                'customer_name': customer_name,
                'phone_number': phone_number,
                'email': email,
                'invoice_number': invoice_number,
                'coupon_code': coupon_code,
                'payment_status': payment_status,
                'payment_method': payment_method,
                'billing_date': timezone.now().date(),
                'invoice_date': timezone.now().date(),
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        
    def get(self, request, *args, **kwargs):
        try:
            # Retrieve shops owned by the authenticated user
            shops = request.user.shop_set.all()

            # Initialize dictionary to store billing information with invoice number as key
            billing_info_dict = {}

            # Iterate over each shop owned by the user
            for shop in shops:
                # Retrieve distinct invoice numbers for the shop
                invoices = BillingDetails.objects.filter(shop=shop).values_list('invoice_number', flat=True).distinct()

                # Iterate over each invoice number
                for invoice_number in invoices:
                    # Retrieve billing details for the invoice in the shop
                    billing_details = BillingDetails.objects.filter(shop=shop, invoice_number=invoice_number)

                    # Serialize the billing details
                    serialized_data = [{
                        'product_name': detail.product_name,
                        'price': detail.price,
                        'quantity': detail.quantity,
                        'total_amount': detail.total_amount
                    } for detail in billing_details]

                    # Extract billing date from the first billing detail entry
                    billing_date = billing_details.first().billing_date

                    # Calculate the total amount for the invoice
                    total_amount = billing_details.aggregate(total=Sum('total_amount'))['total'] or 0

                    # Check if there is a coupon code applied
                    coupon_code = billing_details.first().coupon_code
                    coupon_discount = 0
                    if coupon_code:
                        coupon = Coupon.objects.filter(coupon_code=coupon_code).first()
                        if coupon:
                            coupon_discount = coupon.amount

                    # Calculate grand total after subtracting coupon discount
                    grand_total = total_amount - coupon_discount

                    # Retrieve distinct customer names for the invoice
                    customer_names = billing_details.values_list('customer_name', flat=True).distinct()

                    # Convert the queryset of customer names to a comma-separated string
                    customer_names_str = ', '.join(customer_names)

                    # Check if the invoice number already exists in the dictionary
                    if invoice_number in billing_info_dict:
                        # Append billing details to existing invoice entry
                        billing_info_dict[invoice_number]['billing_details'].extend(serialized_data)
                    else:
                        # Create a new entry for the invoice number
                        billing_info_dict[invoice_number] = {
                            'shop_name': shop.shop_name,
                            'invoice_number': invoice_number,
                            'billing_date': billing_date,  # Move billing date here
                            'total_amount': total_amount,
                            'coupon_code': coupon_code,
                            'grand_total': grand_total,
                            'customer_name': customer_names_str,
                            'billing_details': serialized_data
                        }

            # Convert the dictionary values to a list
            billing_info = list(billing_info_dict.values())

            return Response(billing_info, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

class BillingDeleteView(APIView):
   
    permission_classes = [IsAuthenticated, IsShopOwner]
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            # Extract billing data identifier from URL parameter (e.g., invoice_number)
            invoice_number = self.kwargs.get('invoice_number')

            # Find billing data based on the invoice number
            billing_data = BillingDetails.objects.filter(invoice_number=invoice_number)

            # Check if billing data exists
            if not billing_data.exists():
                return Response({'error': f'Billing data with invoice number {invoice_number} not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Calculate total amount and grand total
            total_amount = sum(detail.total_amount for detail in billing_data)
            coupon_code = billing_data.first().coupon_code
            coupon_discount = 0
            if coupon_code:
                coupon = Coupon.objects.filter(coupon_code=coupon_code).first()
                if coupon:
                    coupon_discount = coupon.amount
            grand_total = total_amount - coupon_discount

            # Serialize the billing data
            billing_details = {
                'customer_name': billing_data.first().customer_name,
                'invoice_number': invoice_number,
                'total_amount': total_amount,
                'coupon_code': coupon_code,
                'grand_total': grand_total,
                'billing_details': [{'product_name': detail.product_name, 'price': detail.price, 'quantity': detail.quantity, 'total_amount': detail.total_amount,'billing_date':detail.billing_date} for detail in billing_data]
            }

            return Response(billing_details, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        try:
            # Extract billing data identifier from URL parameter (e.g., invoice_number)
            invoice_number = self.kwargs.get('invoice_number')

            # Find billing data to delete
            billing_data = BillingDetails.objects.filter(invoice_number=invoice_number)

            # Check if billing data exists
            if not billing_data.exists():
                return Response({'error': f'Billing data with invoice number {invoice_number} not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Delete the billing data
            billing_data.delete()

            return Response({'message': f'Billing data with invoice number {invoice_number} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.db.models import Q


from collections import defaultdict

class GoogleFormResponses(APIView):
    def get(self, request, *args, **kwargs):
        SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
        SERVICE_ACCOUNT_FILE = r'paste your json file path'

        try:
            # Initialize credentials
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            # Build the service
            service = build('forms', 'v1', credentials=creds)

            # Google Form ID
            form_id = 'paste your feedbackform form id'

            # Fetch responses
            response = service.forms().responses().list(formId=form_id).execute()

            # Process responses
            if 'responses' in response:
                existing_responses = set(
                    (response['email'].strip().lower(), response['product_name'].strip().lower(), response['shop_name'].strip().lower())
                    for response in FeedbackFormResponse.objects.values('email', 'product_name', 'shop_name')
                )
                new_responses = []
                for item in response['responses']:
                    answer = item.get('answers', {})
                    extracted_item = {
                        'customer_name': answer.get('662942f2', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value'),
                        'email': answer.get('75a29328', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value'),
                        'phone_number': answer.get('03915ea7', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value'),
                        'shop_name': answer.get('30f16c43', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value').strip().lower(),
                        'product_name': answer.get('54b6f49b', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value').strip().lower(),
                        'rating': answer.get('2dd5e41d', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value'),
                        'feedback': answer.get('6b9c1ded', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value')
                    }

                    # Check if the same response has been processed before
                    response_key = (extracted_item['email'], extracted_item['product_name'], extracted_item['shop_name'])
                    if response_key in existing_responses:
                        # If the same response is found, skip adding it
                        continue

                    # Add the new response to the list of new responses
                    new_responses.append(extracted_item)
                    existing_responses.add(response_key)

                # Bulk insert new responses into the database
                FeedbackFormResponse.objects.bulk_create([
                    FeedbackFormResponse(**item) for item in new_responses
                ])

                # Retrieve all stored responses
                stored_responses = FeedbackFormResponse.objects.all()

                # Serialize the responses
                serialized_responses = FeedbackFormResponseSerializer(stored_responses, many=True)

                return Response({'message': 'Responses fetched and added to the database successfully.', 'responses': serialized_responses.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No responses found.'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




        
from datetime import datetime
from decimal import Decimal
from datetime import timedelta

# class ProfitByShopAndDateRangeView(APIView):
#     def get(self, request, shop_id):
#         try:
#             billing_details = BillingDetails.objects.filter(shop_id=shop_id)
#             if not billing_details.exists():
#                 return Response({"error": "No billing details found for this shop."}, status=status.HTTP_404_NOT_FOUND)

#             start_date = billing_details.earliest('billing_date').billing_date
#             end_date = billing_details.latest('billing_date').billing_date
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         try:
#             profit_data = []

#             current_date = start_date
#             while current_date <= end_date:
#                 daily_profit = Decimal(0)  # Initialize as Decimal
#                 total_selling_price = Decimal(0)
#                 total_product_price = Decimal(0)

#                 for bd in billing_details.filter(billing_date=current_date):
#                     products = Product.objects.filter(product_name=bd.product_name)
#                     for product in products:
#                         # Convert price to Decimal before subtraction
#                         product_price = Decimal(product.price)
#                         # Calculate profit for each billing detail separately
#                         daily_profit += (Decimal(bd.price) - product_price)
#                         total_selling_price += product.selling_price if product.selling_price else 0
#                         total_product_price += product.price

#                 # Check if coupon code was used
#                 coupon_amount = 0
#                 if bd.coupon_code:
#                     try:
#                         coupon = Coupon.objects.get(coupon_code=bd.coupon_code)
#                         coupon_amount = Decimal(coupon.amount)
#                     except Coupon.DoesNotExist:
#                         pass

#                 # Subtract coupon amount from daily profit
#                 daily_profit -= coupon_amount
                
#                 # Only append profit data if both total selling price and total product price are not zero
#                 if total_selling_price != Decimal(0) or total_product_price != Decimal(0):
#                     profit_data.append({
#                         "date": current_date.strftime('%Y-%m-%d'), 
#                         "total_profit": daily_profit,
#                         "total_selling_price": total_selling_price,
#                         "total_product_price": total_product_price
#                     })
#                 current_date += timedelta(days=1)

#             return Response(profit_data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
from django.conf import settings
from django.db.models import Avg

from django.db.models import Avg, IntegerField
from django.db.models.functions import Cast
from django.db.models import FloatField
class RecommendationEmails(APIView):
    def get(self, request, shop_name):
        # Determine the top-rated products for the particular shop
        top_rated_products = FeedbackFormResponse.objects.filter(shop_name__iexact=shop_name).order_by('-rating')[:5]

        # Extract unique product names from the top-rated products
        top_product_names = set([product.product_name for product in top_rated_products])

        # Fetch the email addresses of customers from the billing table
        customers = BillingDetails.objects.filter(shop__shop_name__iexact=shop_name).values_list('email', flat=True).distinct()

        # Iterate through customers and send recommendation emails
        subject = 'Top Rated Product Recommendation'
        from_email = 'your email id'
        for customer_email in customers:
            # Exclude products already purchased by the customer
            purchased_products = BillingDetails.objects.filter(email=customer_email, product_name__in=top_product_names)
            unpurchased_products = top_product_names.difference(set([purchase.product_name for purchase in purchased_products]))
            
            # Construct the message with unpurchased top-rated products
            if unpurchased_products:
                message = f'Dear Customer,\nWe would like to recommend our top-rated products: {", ".join(unpurchased_products)}.'
            else:
                message = 'Dear Customer,\nWe currently do not have any top-rated products to recommend.'

            # Send email to customer
            send_mail(subject, message, from_email, [customer_email])

        return Response({"message": f"Recommendation emails sent successfully for shop: {shop_name}."})


# class ServiceFormResponses(APIView):
#     def get(self, request):
#         # Set up credentials
#         SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
#         SERVICE_ACCOUNT_FILE = r''
#         creds = service_account.Credentials.from_service_account_file(
#             SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#         # Build the service
#         service = build('forms', 'v1', credentials=creds)
#         # Google Form ID
#         form_id = '1el8Lq8wthq639nHKGjrtr6_ntCGu_mJRB0n-1EzfjoU'
#         # Fetch responses
#         response = service.forms().responses().list(formId=form_id).execute()
#         # Process responses
#         if 'responses' in response:
#             for item in response['responses']:
#                 response_id = item['responseId']  # Assuming 'responseId' is the unique identifier
#                 if not ResponseModel.objects.filter(response_id=response_id).exists():
#                     # If response doesn't exist in the table, add it
#                     extracted_response = {}
#                     answers = item.get('answers', {})
#                     extracted_response['response_id'] = response_id
#                     extracted_response['customername'] = answers.get('5e4643fb', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     extracted_response['email'] = answers.get('415854ec', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     extracted_response['mobile'] = answers.get('713d51b0', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     extracted_response['shopname'] = answers.get('1be83740', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     extracted_response['productname'] = answers.get('6a751b69', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     extracted_response['issue_or_service'] = answers.get('0044c083', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
#                     # Save the response to the table
#                     ResponseModel.objects.create(**extracted_response)
#             # Query all responses
#             responses = ResponseModel.objects.all()
#             serializer = ResponseModelSerializer(responses, many=True)  # Use your serializer here
#             return Response({'message': 'Responses added to the table.', 'data': serializer.data})
#         else:
#             return Response({'message': 'No responses found.'}, status=404)
        

class ServiceVerifiedAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve all ServiceVerified instances
        service_verified_objects = ServiceVerified.objects.all()
        serializer = ServiceVerifiedSerializer(service_verified_objects, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = ServiceVerifiedSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            # Check if is_done is True or False
            if data['is_done']:
                data['status'] = "Service Verified"
            else:
                data['status'] = "Pending"
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ServiceVerifiedDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return ServiceVerified.objects.get(pk=pk)
        except ServiceVerified.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        service_verified_instance = self.get_object(pk)
        serializer = ServiceVerifiedSerializer(service_verified_instance)
        return Response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        service_verified_instance = self.get_object(pk)
        serializer = ServiceVerifiedSerializer(service_verified_instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        service_verified_instance = self.get_object(pk)
        service_verified_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

from .tasks import *
from django.http import HttpResponse

def test(request):
    send_offer_reminder_emails.delay()
    return HttpResponse("done")


# def send_offer_emails_view(request):
#     send_offer_reminder.delay()  # Trigger the Celery task asynchronously
#     return HttpResponse("Offer emails will be sent shortly.")


class OfferAPIView(APIView):
    def get(self, request):
        offers = Offer.objects.all()
        serializer = OfferSerializer(offers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OfferSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OfferDetail(APIView):
    """
    Retrieve, update or delete an offer instance.
    """
    def get_object(self, pk):
        return get_object_or_404(Offer, pk=pk)

    def get(self, request, pk, format=None):
        offer = self.get_object(pk)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        offer = self.get_object(pk)
        serializer = OfferSerializer(offer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        offer = self.get_object(pk)
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)   
    


class service_test(APIView):
    def get(self, request):
        # Set up credentials
        SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
        SERVICE_ACCOUNT_FILE = r''  # Update with your service account file path
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # Build the service
        service = build('forms', 'v1', credentials=creds)
        
        # Google Form ID
        form_id = ''  # Update with your Google Form ID
        
        # Fetch responses
        response = service.forms().responses().list(formId=form_id).execute()
        
        # Process responses
        if 'responses' in response:
            for item in response['responses']:
                response_id = item['responseId']  # Assuming 'responseId' is the unique identifier
                if not ResponseModel.objects.filter(response_id=response_id).exists():
                    # If response doesn't exist in the table, add it
                    extracted_response = {}
                    answers = item.get('answers', {})
                    extracted_response['response_id'] = response_id
                    extracted_response['customername'] = answers.get('63712068', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    extracted_response['email'] = answers.get('01d0b201', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    extracted_response['mobile'] = answers.get('748b5e9b', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    extracted_response['shopname'] = answers.get('1d1c0629', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    extracted_response['productname'] = answers.get('67046855', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    extracted_response['issue_or_service'] = answers.get('5482b17a', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', '')
                    # Save the response to the table
                    ResponseModel.objects.create(**extracted_response)
            # Query all responses
            responses = ResponseModel.objects.all()
            serializer = ResponseModelSerializer(responses, many=True)  # Use your serializer here
            return Response({'message': 'Responses added to the table.', 'data': serializer.data})
        else:
            return Response({'message': 'No responses found.'}, status=404)
        

# class feedback_test(APIView):
#     def get(self, request):
#         # Set up credentials
#         SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
#         SERVICE_ACCOUNT_FILE = r'C:\Users\User\crm_backup\CRM-backend\praxis-window-419705-994a674d9526.json'
#         creds = service_account.Credentials.from_service_account_file(
#             SERVICE_ACCOUNT_FILE, scopes=SCOPES)

#         # Build the service
#         service = build('forms', 'v1', credentials=creds)

#         # Google Form ID
#         form_id = '1rqzkEprctmykJPnNGq8VcbkkFNsGQDYMvLglJR0qooo'

#         try:
#             # Fetch responses
#             response = service.forms().responses().list(formId=form_id).execute()
#             # Process responses
#             if 'responses' in response:
#                 return Response(response['responses'])
#             else:
#                 return Response({'message': 'No responses found.'}, status=404)
#         except Exception as e:
#             return Response({'message': str(e)}, status=500)
        
from django.db.models import F
        
from decimal import Decimal

from decimal import Decimal

from django.db.models import Min, Max

from django.db.models import Min, Max

class ProfitByShopAndDateView(APIView):
    def get(self, request, shop_id):
        try:
            billing_details = BillingDetails.objects.filter(shop_id=shop_id)
            if not billing_details.exists():
                return Response({"error": "No billing details found for this shop."}, status=status.HTTP_404_NOT_FOUND)

            start_date = billing_details.aggregate(Min('billing_date'))['billing_date__min']
            end_date = billing_details.aggregate(Max('billing_date'))['billing_date__max']

            profit_data = []

            current_date = start_date
            while current_date <= end_date:
                total_price = Decimal(0)
                total_selling_price = Decimal(0)
                total_coupon_amount = Decimal(0)
                products_sold = []
                product_sold_count = {}

                billing_details_date = billing_details.filter(billing_date=current_date)

                if billing_details_date.exists():
                    for bd in billing_details_date:
                        product = Product.objects.filter(product_name=bd.product_name).first()
                        if product:
                            stock = Stock.objects.filter(pro_company=product.pro_company, productname=product.product_name).first()
                            if stock:
                                current_stock_quantity = stock.quantity
                            else:
                                current_stock_quantity = 0

                            product_price = product.price * bd.quantity
                            total_price += product_price

                            if bd.payment_status == 'paid':
                                product_selling_price = product.selling_price * bd.quantity if product.selling_price else product.price * bd.quantity
                                total_selling_price += product_selling_price

                            if bd.coupon_code:
                                coupon = Coupon.objects.filter(coupon_code=bd.coupon_code).first()
                                if coupon:
                                    total_coupon_amount += Decimal(coupon.amount)

                            if product.product_name in product_sold_count:
                                product_sold_count[product.product_name] += bd.quantity
                            else:
                                product_sold_count[product.product_name] = bd.quantity

                            products_sold.append({
                                "product_name": product.product_name,
                                "quantity_sold": bd.quantity,
                                "current_stock_quantity": current_stock_quantity
                            })

                    profit_data.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "total_price": total_price,
                        "total_selling_price": total_selling_price,
                        "total_coupon_amount": total_coupon_amount,
                        "products_sold": products_sold,
                        "product_sold_count": product_sold_count
                    })

                current_date += timedelta(days=1)

            return Response(profit_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProductSentimentAPIView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product does not exist"}, status=404)
        
        sentiment_counts = product.count_sentiments()
        
        return Response({
            "product_id": product.id,
            "product_name": product.product_name,
            "sentiment_counts": sentiment_counts
        })
