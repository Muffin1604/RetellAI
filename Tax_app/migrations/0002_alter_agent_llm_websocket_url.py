# Generated by Django 5.1.2 on 2024-10-28 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tax_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='llm_websocket_url',
            field=models.CharField(max_length=255),
        ),
    ]
