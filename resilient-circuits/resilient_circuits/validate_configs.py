#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from .constants import MIN_NUM_WORKERS, MAX_NUM_WORKERS
"""Contains a dict to validate the app configs"""

VALIDATE_DICT = {
    "num_workers": {
        "required": False,
        "valid_condition": lambda c: True if c >= MIN_NUM_WORKERS and c <= MAX_NUM_WORKERS else False,
        "invalid_msg": "num_workers must be in the range {} <= {}".format(MIN_NUM_WORKERS, MAX_NUM_WORKERS)
    }
}
