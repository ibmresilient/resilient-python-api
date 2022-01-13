#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""Subtle overwrites for the 'genson' library"""


def custom_add_object(self, obj):
    """
    Overwrite genson.schema.strategies.object.Object.add_object()
    method.

    Basically assign ``self._required`` to always be an empty set()
    """
    properties = set()
    for prop, subobj in obj.items():
        pattern = None

        if prop not in self._properties:
            pattern = self._matching_pattern(prop)

        if pattern is not None:
            self._pattern_properties[pattern].add_object(subobj)
        else:
            properties.add(prop)
            self._properties[prop].add_object(subobj)

        self._required = set()


def main_genson_builder_overwrites(builder):
    """
    An genson.schema.strategies.object.Object's add_object method has been
    customized to set no properties as required by default

    :param builder: (required) absolute path to a app.log file
    :type builder: genson.SchemaBuilder
    """
    for s in builder.STRATEGIES:

        # Overwrite 'strategies.object.Object' 'add_object' method so fields are not 'required' by default
        if s.__module__ == "genson.schema.strategies.object":
            s.add_object = custom_add_object
