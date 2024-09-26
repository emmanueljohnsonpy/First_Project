# Generated by Django 5.0.8 on 2024-09-02 17:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0007_checkoutdetails_before_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkoutdetails',
            name='cart',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='checkout_details', to='carts.cart'),
        ),
    ]
