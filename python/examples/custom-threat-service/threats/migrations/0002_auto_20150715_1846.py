# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('threats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='artifact',
            name='source_class',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='artifact',
            name='type',
            field=models.CharField(max_length=32, choices=[(b'file.content', b'file.content'), (b'file.name', b'file.name'), (b'file.path', b'file.path'), (b'email', b'email'), (b'email.body', b'email.body'), (b'email.header', b'email.header'), (b'email.header.senderAddress', b'email.header.senderAddress'), (b'email.header.senderName', b'email.header.senderName'), (b'email.header.to', b'email.header.to'), (b'hash.md5', b'hash.md5'), (b'hash.sha1', b'hash.sha1'), (b'hash.fuzzy', b'hash.fuzzy'), (b'cert.x509', b'cert.x509'), (b'net.ip', b'net.ip'), (b'net.port', b'net.port'), (b'net.uri', b'net.uri'), (b'net.http.request.header', b'net.http.request.header'), (b'net.http.response.header', b'net.http.response.header'), (b'process.name', b'process.name'), (b'system.name', b'system.name'), (b'system.mutex', b'system.mutex'), (b'system.registry', b'system.registry')]),
        ),
        migrations.AlterField(
            model_name='property',
            name='type',
            field=models.CharField(max_length=32, choices=[(b'string', b'string'), (b'number', b'number'), (b'uri', b'uri'), (b'ip', b'ip'), (b'latlng', b'latlng')]),
        ),
    ]
