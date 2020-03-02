# Generated by Django 2.2.1 on 2019-05-19 23:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('magic_api', '0003_auto_20190519_2035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='card_vector_point',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='magic_api.Card', to_field='name'),
        ),
        migrations.AlterField(
            model_name='deck',
            name='url',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]