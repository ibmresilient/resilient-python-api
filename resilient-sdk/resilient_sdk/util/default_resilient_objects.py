#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
A common place to store any default Resilient Objects.
These objects are used during codegen when default 'placeholders' are needed
"""

import uuid
import time

DEFAULT_UUID_1 = uuid.UUID('bfeec2d4-3770-11e8-ad39-4a0004044aa0')
DEFAULT_UUID_2 = uuid.UUID('bfeec2d4-3770-11e8-ad39-4a0004044aa1')

DEFAULT_TIME = int(time.time() * 1000)

# Used during codegen
DEFAULT_INCIDENT_TYPE = {
    "update_date": DEFAULT_TIME,
    "create_date": DEFAULT_TIME,
    "uuid": str(DEFAULT_UUID_1),
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
    "export_key": "incident/internal_customizations_field",
    "id": 0,
    "input_type": "text",
    "internal": True,
    "name": "internal_customizations_field",
    "read_only": True,
    "text": "Customizations Field (internal)",
    "type_id": 0,
    "uuid": str(DEFAULT_UUID_2)
}
