from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
# Create your models here.
class Shop(models.Model):
    user = models.ManyToManyField(User, default=None)
    shop_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.shop_name

class Stock(models.Model):
    pro_company = models.CharField(max_length=100)
    productname = models.CharField(max_length=100)
    quantity = models.IntegerField()

class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    pro_company = models.CharField(max_length=100,null=True,blank=True)
    image=models.ImageField(upload_to='product/',null=True,blank=True)
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(null=True,blank=True)
    product_link=models.CharField(null=True,blank=True,max_length=600)

    def __str__(self):
        return self.product_name

class Employee(models.Model):
    POSITION_CHOICES = [
        ('Manager', 'Manager'),
        ('Sales Associate', 'Sales Associate'),
        ('Cashier', 'Cashier'),
    ]

    emp_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, choices=POSITION_CHOICES)
    contact_no = models.CharField(max_length=15)
    email = models.EmailField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return self.emp_name
    



class BillingDetails(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, validators=[RegexValidator(r'^\d{10}$', message='Enter a valid phone number.')])
    email = models.EmailField()
    billing_date = models.DateField(auto_now_add=True)
    invoice_date = models.DateField(auto_now_add=True)
    invoice_number = models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    price=models.FloatField()
    quantity=models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=20, blank=True,null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True,null=True)

    def save(self, *args, **kwargs):
        # Calculate total amount based on associated products and quantities
        total_amount = self.price * self.quantity
        
        # Apply coupon code discount if available
        if self.coupon_code:
            try:
                # Assuming a fixed discount amount for the coupon code
                coupon_discount = 10  # Example: Fixed discount of 10 units
                total_amount -= coupon_discount
            except ValueError:
                # Handle case where coupon code does not end with a number
                pass
        
        # Update total_amount field with the calculated total amount
        self.total_amount = total_amount
        
        # Call super to save the instance
        super().save(*args, **kwargs)