# Generated by Django 4.2.3 on 2023-08-02 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_alter_blog_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='date_of_change',
            field=models.DateTimeField(blank=True, null=True, verbose_name='дата последнего изменения'),
        ),
    ]
