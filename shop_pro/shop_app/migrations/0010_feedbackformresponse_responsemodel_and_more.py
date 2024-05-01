# Generated by Django 5.0.2 on 2024-04-13 11:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0009_coupon'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackFormResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=20)),
                ('shop_name', models.CharField(max_length=255)),
                ('product_name', models.CharField(max_length=255)),
                ('rating', models.CharField(max_length=10)),
                ('feedback', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ResponseModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_id', models.CharField(max_length=100, unique=True)),
                ('customername', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('mobile', models.CharField(max_length=15)),
                ('shopname', models.CharField(max_length=100)),
                ('productname', models.CharField(max_length=100)),
                ('issue_or_service', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='billingdetails',
            name='shop',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shop_app.shop'),
        ),
        migrations.AddField(
            model_name='product',
            name='csv_file',
            field=models.FileField(blank=True, null=True, upload_to='csvs/'),
        ),
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('starting_date', models.DateTimeField()),
                ('ending_date', models.DateTimeField()),
                ('offer_description', models.TextField()),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop_app.shop')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceVerified',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_done', models.BooleanField(default=False)),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop_app.responsemodel')),
            ],
        ),
    ]