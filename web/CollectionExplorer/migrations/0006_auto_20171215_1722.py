# Generated by Django 2.0 on 2017-12-15 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0005_auto_20171215_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('path', models.FilePathField(allow_folders=True, path='D:\\Uni\\Masterarbeit\\Beispieldaten\\Wiki_partial_corpus', recursive=True)),
            ],
        ),
        migrations.DeleteModel(
            name='SourceFolder',
        ),
        migrations.AlterField(
            model_name='document',
            name='path',
            field=models.FilePathField(path='D:\\Uni\\Masterarbeit\\Beispieldaten\\Wiki_partial_corpus', recursive=True),
        ),
    ]