""" Classes to serialize models to JSON api """
from rest_framework.serializers import ModelSerializer
from threats.models import Threat, Property

# pylint: disable=too-few-public-methods


class PropertySerializer(ModelSerializer):

    """ Serializes properties of the threat record """
    class Meta(object):

        """ Hook up Properties object for serialization """
        model = Property
        fields = ('type', 'name', 'value',)


class ThreatSerializer(ModelSerializer):

    """ Serializes a complete threat record """
    props = PropertySerializer(many=True, read_only=True)

    class Meta(object):

        """ Hook up Threat record object for serialization """
        model = Threat
        fields = ('props',)
