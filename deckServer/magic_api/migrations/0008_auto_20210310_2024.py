# Generated by Django 3.0.3 on 2021-03-10 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magic_api', '0007_auto_20210310_2003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='rarity',
            field=models.IntegerField(choices=[(0, 'common'), (1, 'uncommon'), (2, 'rare'), (3, 'mythic'), (4, 'special'), (5, 'bonus')], default=0),
        ),
    ]
