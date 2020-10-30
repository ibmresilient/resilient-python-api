#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Contains a dict to validate the app configs"""

VALIDATE_DICT = {
    "num_workers": {
        "required": False,
        "valid_condition": lambda c: True if c >= 1 and c <= 50 else False,
        "invalid_msg": "num_workers must be in the range 1 <= 50"
    }
}
