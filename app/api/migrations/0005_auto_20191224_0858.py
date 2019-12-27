# Generated by Django 2.1.11 on 2019-12-24 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_references_chemical_list_fileds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paper',
            name='issn_linking',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='paper',
            name='journal',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='paper',
            name='medline_ta',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='paper',
            name='other_id',
            field=models.CharField(max_length=255),
        ),
    ]
