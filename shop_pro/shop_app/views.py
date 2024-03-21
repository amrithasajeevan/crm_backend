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
                    return Response({'error': 'Shop not found or not associated with the user'}, status=status.HTTP_404_NOT_FOUND)
                pro_company = request.data.get('pro_company', None)
                product_name = request.data.get('product_name', None)
                if pro_company and product_name:
                    try:
                        stock = Stock.objects.get(pro_company=pro_company, productname=product_name)
                    except Stock.DoesNotExist:
                        return Response({'error': 'Stock not found for the given pro_company and productname'}, status=status.HTTP_404_NOT_FOUND)

                    # Update the serializer data with the correct stock instance
                    serializer.validated_data['stock'] = stock
                    serializer.validated_data['stock_quantity'] = stock.quantity
                    

                    # Assuming the serializer.save() will automatically associate the shop and other fields
                    serializer.save(shop=shop)

                    # Include stock_quantity in the response
                    response_data = serializer.data
                    response_data['stock_quantity'] = stock.quantity

                    return Response({'message': 'Product successfully added', 'data': response_data}, status=status.HTTP_201_CREATED)
                else:
                    return Response({'error': 'pro_company and productname are required for stock lookup'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Shop name is required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

 

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
        response_data = serializer.data
        response_data['stock_quantity'] = product.stock_quantity  # Manually add stock_quantity to the response
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
            customer_name = request.data.get('customer_name')
            phone_number = request.data.get('phone_number')
            email = request.data.get('email')
            invoice_number = request.data.get('invoice_number')
            coupon_code = request.data.get('coupon_code')
            payment_status = request.data.get('payment_status')
            payment_method = request.data.get('payment_method')
            products_data = request.data.get('products')

            # Initialize variables to store total amount and billing details list
            total_amount = 0
            billing_details_list = []

            for product_data in products_data:
                product_name = product_data['product_name']
                quantity = product_data['quantity']

                # Retrieve the product based on the provided product_name
                product = Product.objects.get(product_name=product_name)

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
                    billing_date=datetime.date.today(),
                    invoice_date=datetime.date.today(),
                )
                billing_details.save()

                # Append billing details to the list
                billing_details_list.append({
                    'id': billing_details.id,
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
                'billing_date': datetime.date.today(),
                'invoice_date': datetime.date.today()
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, *args, **kwargs):
        try:
            # Retrieve distinct customer names and invoice numbers
            customers_and_invoices = BillingDetails.objects.values('customer_name', 'invoice_number').distinct()

            # Initialize list to store billing information
            billing_info = []

            # Retrieve billing details for each distinct customer and invoice number
            for item in customers_and_invoices:
                customer_name = item['customer_name']
                invoice_number = item['invoice_number']
                
                # Retrieve billing details based on customer name and invoice number
                billing_details = BillingDetails.objects.filter(customer_name=customer_name, invoice_number=invoice_number)
                
                # Serialize the billing details
                serialized_data = [{'product_name': detail.product_name, 'price': detail.price, 'quantity': detail.quantity, 'total_amount': detail.total_amount} for detail in billing_details]
                
                # Calculate the total amount for the invoice
                total_amount = sum(detail.total_amount for detail in billing_details)

                # Check if there is a coupon code applied
                coupon_code = billing_details.first().coupon_code
                coupon_discount = 0
                if coupon_code:
                    coupon = Coupon.objects.filter(coupon_code=coupon_code).first()
                    if coupon:
                        coupon_discount = coupon.amount

                # Calculate grand total after subtracting coupon discount
                grand_total = total_amount - coupon_discount

                # Add customer name, invoice number, total amount, coupon code, and grand total to the list
                billing_info.append({
                    'customer_name': customer_name,
                    'invoice_number': invoice_number,
                    'total_amount': total_amount,
                    'coupon_code': coupon_code,
                    'grand_total': grand_total,
                    'billing_details': serialized_data
                })

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
                'billing_details': [{'product_name': detail.product_name, 'price': detail.price, 'quantity': detail.quantity, 'total_amount': detail.total_amount} for detail in billing_data]
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