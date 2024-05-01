from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import csv
from io import StringIO
# Create your models here.
class Shop(models.Model):
    user = models.ManyToManyField(User, default=None)
    shop_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.shop_name
    def calculate_total_profit(self, date=None):
        total_profit = 0
        billing_details = BillingDetails.objects.filter(shop=self)
        
        if date:
            billing_details = billing_details.filter(billing_date=date)

        for billing_detail in billing_details:
            # Retrieve product associated with the billing detail
            product_name = billing_detail.product_name
            product = Product.objects.filter(shop=self, product_name=product_name).first()

            # Ensure product exists before calculating profit
            if product:
                # Calculate profit for the product
                profit = product.calculate_profit()

                # Add profit to total profit
                total_profit += profit

        return total_profit
    

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
    csv_file=models.FileField(null=True,upload_to='csvs/',blank=True)


    def __str__(self):
        return self.product_name
    def calculate_profit(self):
        return self.selling_price - self.price if self.selling_price else 0
    def count_sentiments(self):
        if self.csv_file:
            # Read the CSV file
            csv_data = self.csv_file.read().decode('utf-8')
            csv_file = StringIO(csv_data)

            # Parse CSV data
            reader = csv.DictReader(csv_file)
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            for row in reader:
                sentiment = row['Status'].strip().lower()
                if sentiment == 'positive':
                    positive_count += 1
                elif sentiment == 'negative':
                    negative_count += 1
                elif sentiment == 'neutral':
                    neutral_count += 1
            
            return {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        else:
            return {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }

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
    shop=models.ForeignKey(Shop,on_delete=models.CASCADE,null=True)
    def __str__(self):
        return self.invoice_number
    
    

class Coupon(models.Model):
    coupon_code=models.CharField(max_length=100)
    amount = models.IntegerField()

class FeedbackFormResponse(models.Model):
    customer_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    shop_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    rating = models.CharField(max_length=10)
    feedback = models.TextField()

    def __str__(self):
        return self.customer_name
    

class ResponseModel(models.Model):
    response_id = models.CharField(max_length=100, unique=True)
    customername = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    shopname = models.CharField(max_length=100)
    productname = models.CharField(max_length=100)
    issue_or_service = models.CharField(max_length=255)

    def __str__(self):
        return f"Response {self.response_id}"
    
class ServiceVerified(models.Model):
    response = models.ForeignKey(ResponseModel, on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        if self.is_done:
            return f"Service Verified for Response {self.response.response_id}"
        else:
            return f"Pending for Response {self.response.response_id}"
        
class Offer(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    starting_date = models.DateTimeField()
    ending_date = models.DateTimeField()
    offer_description = models.TextField()

    def __str__(self):
        return self.title
    @classmethod
    def get_upcoming_offers(cls):
        from datetime import timedelta
        from django.utils import timezone
        
        start_date_threshold = timezone.now() + timedelta(days=2)
        return cls.objects.filter(starting_date__date=start_date_threshold.date())

