# Generated by Django 5.1.2 on 2024-10-31 21:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books_operator', '0007_alter_cart_book'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cart',
            unique_together={('customer', 'book')},
        ),
    ]