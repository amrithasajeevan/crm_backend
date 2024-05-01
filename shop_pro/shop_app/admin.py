from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Coupon)
admin.site.register(BillingDetails)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(FeedbackFormResponse)
admin.site.register(ResponseModel)