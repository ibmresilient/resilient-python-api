#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
Used by resilient-circuits for customize.
Used by resilient-sdk for reloading the customize.py file
"""


class Definition(object):
    """A definition that can be loaded for resilient-circuits customize."""

    def __init__(self, value):
        self.value = value


class TypeDefinition(Definition):
    """Definition of a type with fields"""
    pass


class MessageDestinationDefinition(Definition):
    """Definition of a message destination"""
    pass


class FunctionDefinition(Definition):
    """Definition of a function"""
    pass


class ActionDefinition(Definition):
    """Definition of a custom action (rule)"""
    pass


class ImportDefinition(Definition):
    """Definition of a set of importable customizations"""
    pass
