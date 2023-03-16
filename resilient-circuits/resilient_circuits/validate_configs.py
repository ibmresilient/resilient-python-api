#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from .constants import (APP_CONFIG_LOG_BACKUP_COUNT, APP_CONFIG_LOG_MAX_BYTES,
                        MAX_NUM_WORKERS, MIN_BACKUP_COUNT, MIN_LOG_BYTES,
                        MIN_NUM_WORKERS)

"""Contains a dict to validate the app configs"""

VALIDATE_DICT = {
    "num_workers": {
        "required": False,
        "valid_condition": lambda c: True if c >= MIN_NUM_WORKERS and c <= MAX_NUM_WORKERS else False,
        "invalid_msg": "num_workers must be in the range {} <= {}".format(MIN_NUM_WORKERS, MAX_NUM_WORKERS)
    },
    APP_CONFIG_LOG_MAX_BYTES: {
        "required": False,
        "valid_condition": lambda c: True if c == 0 or c >= MIN_LOG_BYTES else False,
        "invalid_msg": "{} must be either 0 or >= {}".format(APP_CONFIG_LOG_MAX_BYTES, MIN_LOG_BYTES)
    },
    APP_CONFIG_LOG_BACKUP_COUNT: {
        "required": False,
        "valid_condition": lambda c: True if c >= MIN_BACKUP_COUNT else False,
        "invalid_msg": "{} must be a positive value".format(APP_CONFIG_LOG_BACKUP_COUNT)
    }
}
