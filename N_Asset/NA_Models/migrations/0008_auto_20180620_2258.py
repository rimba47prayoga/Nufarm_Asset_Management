# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-20 22:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NA_Models', '0007_auto_20180620_2257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nastock',
            name='isbroken',
            field=models.IntegerField(db_column='IsBroken', null=True),
        ),
        migrations.AlterField(
            model_name='nastock',
            name='tisnew',
            field=models.IntegerField(db_column='TIsNew', null=True),
        ),
        migrations.AlterField(
            model_name='nastock',
            name='tisrenew',
            field=models.IntegerField(db_column='TIsRenew', null=True),
        ),
        migrations.AlterField(
            model_name='nastock',
            name='tisused',
            field=models.IntegerField(db_column='TIsUsed', null=True),
        ),
    ]
