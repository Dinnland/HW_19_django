# Generated by Django 4.2.3 on 2023-08-12 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0017_product_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sign_of_publication',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='признак публикации'),
        ),
    ]
