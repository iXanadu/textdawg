# Generated by Django 5.0 on 2023-12-28 18:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MessageUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fubId', models.CharField(max_length=255, unique=True)),
                ('phone_number', models.CharField(max_length=50, unique=True)),
                ('firstname', models.CharField(max_length=100)),
                ('lastname', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message_count', models.IntegerField(default=0)),
                ('is_opted_out', models.BooleanField(default=False)),
                ('is_banned', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='MessageHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('fubId', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=50)),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant')], max_length=10)),
                ('message', models.TextField()),
                ('status', models.CharField(max_length=100)),
                ('message_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_history', to='main.messageuser')),
            ],
        ),
    ]
