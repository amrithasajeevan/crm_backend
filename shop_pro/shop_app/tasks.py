from .models import *

from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BillingDetails, Offer
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# @shared_task(bind=True)
# def  test_func(self):
#     for i in range(10):
#         print(i)
#     return "done"

@shared_task
def send_offer_reminder_emails():
    from datetime import timedelta
    from django.utils import timezone

    # Get offers that start in two days
    start_date_threshold = timezone.now() + timedelta(days=2)
    upcoming_offers = Offer.objects.filter(starting_date__date=start_date_threshold.date())

    for offer in upcoming_offers:
        # Construct email content
        subject = f"Upcoming Offer: {offer.title} at {offer.shop.shop_name}"
        message = f"Hi,\n\nAn offer is starting soon at {offer.shop.shop_name}!\n\n"
        message += f"Offer: {offer.title}\n"
        message += f"Description: {offer.offer_description}\n"
        message += f"Starting Date: {offer.starting_date}\n"
        message += f"Ending Date: {offer.ending_date}\n\n"
        message += "Don't miss out on this great offer!\n\nBest regards,\nYour Shop Team"

        # Get customers for the offer from BillingDetails
        customers = BillingDetails.objects.filter(email__isnull=False).values_list('customer_name', 'email')
        
        for customer_name, customer_email in customers:
            send_mail(
                subject,
                message,
                'amrithababy142@gmail.com',  # Update with your email
                [customer_email],
            )