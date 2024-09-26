# Generated by Django 5.0.8 on 2024-08-27 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='action',
            field=models.CharField(choices=[('block', 'Block'), ('unblock', 'Unblock')], default='block', max_length=10, verbose_name='Action'),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('expired', 'Expired')], default='active', max_length=10, verbose_name='Status'),
        ),
    ]
