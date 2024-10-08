# Generated by Django 5.0.6 on 2024-06-26 05:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('brand_management', '0002_brand_is_deleted'),
        ('category_management', '0002_category_is_deleted'),
    ]

    operations = [
        migrations.CreateModel(
            name='Products',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=100)),
                ('product_description', models.TextField(max_length=5000)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('offer_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('thumbnail', models.ImageField(null=True, upload_to='images/thumbnail_images')),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('product_brand', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='brand_management.brand')),
                ('product_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='category_management.category')),
            ],
        ),
        migrations.CreateModel(
            name='Product_images',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images', models.ImageField(default='F:\\week-task\\Project\\images\\ noimage.jpg', upload_to='images/product_images')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_management.products')),
            ],
        ),
    ]
