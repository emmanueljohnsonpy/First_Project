# Generated by Django 5.0.8 on 2024-10-01 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0042_alter_order_coupon_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon_name',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
