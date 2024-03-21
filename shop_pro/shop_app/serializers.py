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
        user = instance.user.first()
        if user:
            representation['user'] = user.username
        return representation


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'pro_company', 'productname', 'quantity']


class ProductSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)

    class Meta:
        model = Product
        fields = ['id','shop_name','image','pro_company','product_name', 'description', 'price', 'selling_price','stock_quantity']

    def get_stock_quantity(self, obj):
        # Retrieve stock quantity for the product
        return obj.stock_quantity if obj.stock else None


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


class BillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingDetails
        fields = ['id', 'customer_name', 'phone_number', 'email', 'billing_date', 'invoice_date', 'invoice_number', 'product_name', 'price', 'quantity', 'total_amount', 'coupon_code', 'payment_status', 'payment_method']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'coupon_code', 'amount']