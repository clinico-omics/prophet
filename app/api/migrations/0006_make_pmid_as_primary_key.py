# Generated by Django 2.1.11 on 2019-12-24 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20191224_0858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paper',
            options={'ordering': ('pmid',)},
        ),
        migrations.RemoveField(
            model_name='paper',
            name='id',
        ),
        migrations.AlterField(
            model_name='paper',
            name='pmid',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
