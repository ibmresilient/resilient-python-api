# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artifact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=32)),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=80)),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Threat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
            ],
        ),
        migrations.AddField(
            model_name='property',
            name='threat',
            field=models.ForeignKey(related_name='props', to='threats.Threat'),
        ),
        migrations.AddField(
            model_name='artifact',
            name='threat',
            field=models.ForeignKey(related_name='artifacts', to='threats.Threat'),
        ),
    ]
