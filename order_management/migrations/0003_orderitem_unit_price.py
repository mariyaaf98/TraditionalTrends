# Generated by Django 5.0.6 on 2024-07-25 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_management', '0002_alter_order_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
