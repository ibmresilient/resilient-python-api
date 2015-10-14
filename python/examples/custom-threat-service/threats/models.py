""" Threat service models are defined herein """
from __future__ import unicode_literals

from django.db import models

# pylint: disable=too-few-public-methods

ARTIFACT_TYPES = [
    "file.content",
    "file.name",
    "file.path",
    "email",
    "email.body",
    "email.header",
    "email.header.sender_address",
    "email.header.sender_name",
    "email.header.to",
    "hash.md5",
    "hash.sha1",
    "hash.fuzzy",
    "cert.x509",
    "net.ip",
    "net.name",
    "net.port",
    "net.uri",
    "net.http.request.header",
    "net.http.response.header",
    "process.name",
    "system.name",
    "system.mutex",
    "system.registry",
    "system.service.name",
]

ARTIFACT_TYPE_CHOICES = ((artifact_type, artifact_type) for artifact_type in ARTIFACT_TYPES)

PROPERTY_TYPES = [
    "string",
    "number",
    "uri",
    "ip",
    "latlng",
]

PROPERTY_TYPE_CHOICES = ((property_type, property_type) for property_type in PROPERTY_TYPES)


class Threat(models.Model):

    """
    This model represents a (potential) threat instance.
    Each threat has multiple artifacts which are properties of the threat record.
    Each hit for an artifact search (ArtifactHit) is one of these Threat objects
    """
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


class Artifact(models.Model):

    """
    This model represents a single artifact facet to a threat instance
    """
    threat = models.ForeignKey(Threat, related_name="artifacts")

    type = models.CharField(max_length=32, choices=ARTIFACT_TYPE_CHOICES)
    value = models.TextField()
    source_class = models.CharField(max_length=80, null=True, blank=True)

    def __str__(self):
        return "{} - {} ({})".format(self.id, self.value[:80], self.type)


class Property(models.Model):

    """
    This model represents properties of an identified threat record
    """
    threat = models.ForeignKey(Threat, related_name="props")

    type = models.CharField(max_length=32, choices=PROPERTY_TYPE_CHOICES)
    name = models.CharField(max_length=80)
    value = models.TextField()

    def __str__(self):
        return "{} ({})".format(self.name, self.type)
