# Generated by Django 3.0.3 on 2021-03-10 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magic_api', '0006_auto_20200624_0510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='rarity',
            field=models.IntegerField(choices=[(0, 'common'), (1, 'uncommon'), (2, 'rare'), (3, 'mythic'), (4, 'special')], default=0),
        ),
    ]
