#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from .constants import MAX_NUM_WORKERS
"""Contains a dict to validate the app configs"""

VALIDATE_DICT = {
    "num_workers": {
        "required": False,
        "valid_condition": lambda c: True if c >= 1 and c <= MAX_NUM_WORKERS else False,
        "invalid_msg": "num_workers must be in the range 1 <= {}".format(MAX_NUM_WORKERS)
    }
}
