# Generated by Django 5.0.8 on 2024-09-02 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_ordereditems'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordereditems',
            name='order_number',
            field=models.CharField(blank=True, max_length=6, null=True, unique=True),
        ),
    ]
