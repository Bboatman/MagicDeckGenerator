# Generated by Django 2.2.1 on 2019-05-19 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magic_api', '0002_auto_20190519_2009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='card_type',
            field=models.FloatField(default=0),
        ),
    ]
