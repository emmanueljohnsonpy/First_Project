# Generated by Django 5.0.8 on 2024-10-02 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0025_alter_product_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='offer_name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
