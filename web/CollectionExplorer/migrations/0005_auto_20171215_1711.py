# Generated by Django 2.0 on 2017-12-15 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_remove_document_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='content',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='document',
            name='path',
            field=models.FilePathField(default=''),
            preserve_default=False,
        ),
    ]
