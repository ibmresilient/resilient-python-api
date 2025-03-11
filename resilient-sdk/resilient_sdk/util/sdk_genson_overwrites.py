#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""Subtle overwrites for the 'genson' library"""


from genson.schema.node import SchemaNode
from genson.schema.builder import SchemaBuilder


class CustomSchemaNode(SchemaNode):
    """
    Custom class to overwrite genson.schema.node.SchemaNode.to_schema method
    """

    def to_schema(self):
        """
        Custom method to convert the current schema to a `dict`.

        For any ``null`` type we return an empty dict,
        pertaining that any datatype will be valid for a null value
        """
        types = set()
        generated_schemas = []
        for active_strategy in self._active_strategies:
            generated_schema = active_strategy.to_schema()
            if len(generated_schema) == 1 and 'type' in generated_schema:
                types.add(generated_schema['type'])
            else:
                generated_schemas.append(generated_schema)

        if types:
            if len(types) == 1:
                (types,) = types

                # The only overwrite change is if the type is "null" we
                # add an blank schema for this node, thus allowing the overall schema
                # to accept any datatype for a 'null' value
                if types == "null":
                    return {}

            else:
                types = sorted(types)
            generated_schemas = [{'type': types}] + generated_schemas
        if len(generated_schemas) == 1:
            (result_schema,) = generated_schemas
        elif generated_schemas:
            result_schema = {'anyOf': generated_schemas}
        else:
            result_schema = {}

        return result_schema


class CustomSchemaBuilder(SchemaBuilder):
    """
    Custom genson.schema.builder.SchemaBuilder to
    specify a CustomSchemaNode Class
    """

    def __init__(self, schema_uri='DEFAULT'):
        self.NODE_CLASS = CustomSchemaNode
        super().__init__(schema_uri)


def _custom_add_object(self, obj):
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
            s.add_object = _custom_add_object
