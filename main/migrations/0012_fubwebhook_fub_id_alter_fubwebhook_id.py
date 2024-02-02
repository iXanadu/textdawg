# Generated by Django 5.0.1 on 2024-02-01 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_fubwebhook'),
    ]

    operations = [
        migrations.AddField(
            model_name='fubwebhook',
            name='fub_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='fubwebhook',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
