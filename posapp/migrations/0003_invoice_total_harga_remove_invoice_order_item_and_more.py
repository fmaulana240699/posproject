# Generated by Django 4.1.7 on 2024-10-11 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posapp', '0002_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='total_harga',
            field=models.IntegerField(null=True),
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='order_item',
        ),
        migrations.AddField(
            model_name='invoice',
            name='order_item',
            field=models.ManyToManyField(to='posapp.order'),
        ),
    ]
