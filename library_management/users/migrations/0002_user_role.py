# Generated by Django 5.1.9 on 2025-05-27 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('member', 'Member'), ('librarian', 'Librarian'), ('admin', 'Admin')], default='member', max_length=20),
        ),
    ]
