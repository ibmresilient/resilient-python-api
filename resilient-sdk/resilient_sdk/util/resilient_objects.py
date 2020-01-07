#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
A common place to store any reference to Resilient CONSTANT Objects or Types
"""

import uuid
import time

DEFAULT_INCIDENT_TYPE_UUID = uuid.UUID('bfeec2d4-3770-11e8-ad39-4a0004044aa0')
DEFAULT_INCIDENT_FIELD_UUID = uuid.UUID('bfeec2d4-3770-11e8-ad39-4a0004044aa1')

DEFAULT_TIME = int(time.time() * 1000)

# Used during codegen
DEFAULT_INCIDENT_TYPE = {
    "update_date": DEFAULT_TIME,
    "create_date": DEFAULT_TIME,
    "uuid": str(DEFAULT_INCIDENT_TYPE_UUID),
    "description": "Customization Packages (internal)",
    "export_key": "Customization Packages (internal)",
    "name": "Customization Packages (internal)",
    "enabled": False,
    "system": False,
    "parent_id": None,
    "hidden": False,
    "id": 0
}

# Used during codegen
DEFAULT_INCIDENT_FIELD = {
    "export_key": u"incident/internal_customizations_field",
    "id": 0,
    "input_type": "text",
    "internal": True,
    "name": "internal_customizations_field",
    "read_only": True,
    "text": "Customizations Field (internal)",
    "type_id": 0,
    "uuid": str(DEFAULT_INCIDENT_FIELD_UUID)
}

# Default field names we should ignore (mainly in docgen)
IGNORED_INCIDENT_FIELDS = [
    u"incident/internal_customizations_field",
    u"incident/inc_training"
]


class ResilientObjMap(object):
    """
    A single location to map Resilient Objects
    access names in an export

    E.g. some are 'programmatic_name' others are 'name'
    """

    MESSAGE_DESTINATIONS = "programmatic_name"
    FUNCTIONS = "export_key"
    WORKFLOWS = "programmatic_name"
    RULES = "name"  # Also known as ACTIONS
    FIELDS = "name"
    INCIDENT_ARTIFACT_TYPES = "programmatic_name"
    DATATABLES = "type_name"
    TASKS = "programmatic_name"
    PHASES = "export_key"
    SCRIPTS = "export_key"


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
