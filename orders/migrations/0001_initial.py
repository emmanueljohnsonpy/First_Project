# Generated by Django 5.0.8 on 2024-08-24 06:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('tax', models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True)),
                ('grand_total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Processing', 'Processing'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'), ('Return Pending', 'Return Pending'), ('Return Cancelled', 'Return Cancelled'), ('Return Success', 'Return Success')], default='Pending', max_length=20, null=True)),
                ('payment_method', models.CharField(max_length=50, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('order_number', models.CharField(blank=True, max_length=6, null=True, unique=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(null=True)),
                ('sub_total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='orders.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='store.product')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(max_length=50, null=True)),
                ('payment_status', models.CharField(default='Pending', max_length=20, null=True)),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('order', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='orders.order')),
            ],
        ),
    ]
