# Generated by Django 5.1.5 on 2025-04-15 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('welcome', '0032_answers_pair_options_order_options_pair'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='textbook',
            name='isbn',
            field=models.CharField(blank=True, max_length=300, null=True, unique=True),
        ),
    ]
