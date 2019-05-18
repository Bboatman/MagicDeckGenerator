# Generated by Django 2.2.1 on 2019-05-18 16:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('multiverse_id', models.BigIntegerField(default=0)),
                ('name', models.CharField(max_length=200)),
                ('rarity', models.IntegerField(choices=[(0, 'common'), (1, 'uncommon'), (2, 'rare'), (3, 'mythic')], default=0)),
                ('card_type', models.CharField(max_length=200)),
                ('toughness', models.CharField(max_length=200)),
                ('power', models.CharField(max_length=200)),
                ('cmc', models.BigIntegerField(default=0)),
                ('color_identity', models.IntegerField(choices=[(0, 'C'), (1, 'R'), (2, 'U'), (3, 'G'), (4, 'B'), (5, 'W'), (6, 'RU'), (7, 'RG'), (8, 'RB'), (9, 'RW'), (10, 'UG'), (11, 'UB'), (12, 'UW'), (13, 'GB'), (14, 'GW'), (15, 'BW'), (16, 'RUG'), (17, 'RUB'), (18, 'RUW'), (19, 'RGB'), (20, 'RGW'), (21, 'RBW'), (22, 'UGB'), (23, 'UGW'), (24, 'UBW'), (25, 'GBW'), (26, 'RUGB'), (27, 'RUGW'), (28, 'RUBW'), (29, 'RGBW'), (30, 'UGBW'), (31, 'RUGBW')], default=0)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('deck_size', models.BigIntegerField(default=0)),
                ('unique_count', models.BigIntegerField(default=0)),
                ('name', models.CharField(max_length=200)),
                ('url', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Deck_Detail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('count', models.BigIntegerField(default=0)),
                ('significance', models.FloatField(default=0)),
                ('card_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='magic_api.Card')),
                ('deck_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='magic_api.Deck')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Card_Vector_Point',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('x_value', models.FloatField(default=0)),
                ('y_value', models.FloatField(default=0)),
                ('algorithm', models.CharField(max_length=200)),
                ('alg_weight', models.BigIntegerField(default=0)),
                ('card_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='magic_api.Card')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
    ]
