#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Common Helper Functions for the resilient-sdk"""

import logging
from resilient import ArgumentParser, get_config_file, get_client

# Temp fix to handle the resilient module logs
logging.getLogger("resilient.co3").addHandler(logging.StreamHandler())
# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


def get_resilient_client():
    # TODO: add doc string and unit test
    config_parser = ArgumentParser(config_file=get_config_file())
    opts = config_parser.parse_known_args()[0]
    return get_client(opts)
