# Generated by Django 5.1.2 on 2024-10-31 14:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books_operator', '0006_alter_cart_book'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='book',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books_operator.book'),
        ),
    ]
