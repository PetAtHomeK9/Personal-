# Generated by Django 5.0.7 on 2024-11-07 12:00

import BotCommerce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BotCommerce', '0005_alter_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(max_length=255, verbose_name=BotCommerce.models.Category),
        ),
    ]
