""" Register models to be able to be edited from the admin interface """
from django.contrib import admin

from threats.models import Threat, Artifact, Property

admin.site.register(Threat)
admin.site.register(Artifact)
admin.site.register(Property)
