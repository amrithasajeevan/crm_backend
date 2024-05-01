from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']  # Add other fields here as needed
        extra_kwargs = {'password': {'write_only': True}}  # Ensure password is write-only

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    

class loginserializer(serializers.Serializer):
    username=serializers.CharField(max_length=30)
    password=serializers.CharField(max_length=30)



    
class ShopSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), many=True)

    class Meta:
        model = Shop
        fields = ['id', 'user', 'shop_name', 'address', 'contact_no', 'email']

    def create(self, validated_data):
        users_data = validated_data.pop('user')
        shop = Shop.objects.create(**validated_data)
        for username in users_data:
            user = User.objects.get(username=username)
            shop.user.add(user)
        return shop

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = [user.username for user in instance.user.all()]
        return representation

    def update(self, instance, validated_data):
        users_data = validated_data.pop('user', None)
        if users_data is not None:
            if isinstance(users_data, str):  # If a single username is provided
                instance.user.clear()
                user = User.objects.get(username=users_data)
                instance.user.add(user)
            else:  # If a list of usernames is provided
                instance.user.clear()
                for username in users_data:
                    user = User.objects.get(username=username)
                    instance.user.add(user)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_internal_value(self, data):
        if isinstance(data.get('user'), str):
            data['user'] = [data['user']]
        return super().to_internal_value(data)

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'pro_company', 'productname', 'quantity']


class ProductSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    stock_quantity = serializers.SerializerMethodField()  # Add this line

    class Meta:
        model = Product
        fields = ['id', 'shop_name', 'image', 'pro_company', 'product_name', 'description', 'price', 'selling_price', 'stock_quantity', 'csv_file']
        extra_kwargs = {
            'product_link': {'required': False}
        }
    def get_stock_quantity(self, obj):
        # Retrieve stock quantity for the product
        return obj.stock_quantity if obj.stock else None


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


class BillingDetailsSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    class Meta:
        model = BillingDetails
        fields = ['id','shop_name', 'customer_name', 'phone_number', 'email', 'billing_date', 'invoice_date', 'invoice_number', 'product_name', 'price', 'quantity', 'total_amount', 'coupon_code', 'payment_status', 'payment_method']
        extra_kwargs={
            'coupon_code':{'required':False},
            'invoice_number':{'required':True}
        }

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'coupon_code', 'amount']

class FeedbackFormResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackFormResponse
        fields = '__all__'

class ResponseModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseModel
        fields = ['id','response_id', 'customername', 'email', 'mobile', 'shopname', 'productname', 'issue_or_service']


class ServiceVerifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVerified
        fields = ['id','response', 'is_done']


class OfferSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name')

    class Meta:
        model = Offer
        fields = ['id', 'shop_name', 'title', 'starting_date', 'ending_date', 'offer_description']

    def create(self, validated_data):
        shop_name = validated_data['shop']['shop_name']
        shop = Shop.objects.get(shop_name=shop_name)
        validated_data['shop'] = shop
        return Offer.objects.create(**validated_data)