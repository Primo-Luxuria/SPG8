# Generated by Django 5.1.5 on 2025-03-18 05:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("welcome", "0003_remove_userprofile_owner_userprofile_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="course",
            name="participants",
        ),
        migrations.RemoveField(
            model_name="test",
            name="creator",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="user",
        ),
        migrations.AddField(
            model_name="answeroption",
            name="answer_graphic",
            field=models.ImageField(
                blank=True, null=True, upload_to="answer_graphics/"
            ),
        ),
        migrations.AddField(
            model_name="answeroption",
            name="response_feedback_graphic",
            field=models.ImageField(blank=True, null=True, upload_to=""),
        ),
        migrations.AddField(
            model_name="answeroption",
            name="response_feedback_text",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="course",
            name="teachers",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={"userprofile__role": "teacher"},
                related_name="courses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
