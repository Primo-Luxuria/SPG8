# Generated by Django 5.1.5 on 2025-03-24 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('welcome', '0021_testpart_testsection_testquestion_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='part_structure',
            field=models.JSONField(blank=True, help_text='JSON representation of the test part structure', null=True),
        ),
    ]
