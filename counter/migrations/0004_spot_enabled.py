# Generated by Django 3.2.7 on 2021-10-12 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("counter", "0003_auto_20211007_1714"),
    ]

    operations = [
        migrations.AddField(
            model_name="spot",
            name="enabled",
            field=models.BooleanField(default=True),
        ),
    ]
