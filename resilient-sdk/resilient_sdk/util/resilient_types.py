#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.


class ResilientTypeIds(object):
    """A single location for Resilient Object Type Ids"""

    INCIDENT = 0
    TASK = 1
    NOTE = 2
    MILESTONE = 3
    ARTIFACT = 4
    ATTACHMENT = 5
    ACTION_INVOCATION = 6
    ORG = 7
    DATATABLE = 8
    LAYOUT = 9
    MESSAGE_DESTINATION = 10
    FUNCTION = 11


class ResilientFieldTypes(object):
    """A single location for Resilient Field Types"""

    ACTIVITY_FIELD = "actioninvocation"
    FUNCTION_INPUT = "__function"
