#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
Common place for helper functions used in tests
"""

import io
import os
import json
from tests.shared_mock_data import mock_paths


def read_mock_json(template_name):
    """
    Read a mock JSON file from .shared_mock_data/resilient_api_data/template_name
    Return it as a Dictionary
    """
    return_json = {}
    template_path = os.path.join(mock_paths.RESILIENT_API_DATA, template_name)
    with io.open(template_path, "r", encoding="utf-8") as template_file:
        return_json = json.load(template_file)
    return return_json


def verify_expected_list(list_expected_strs, list_actual_strs):
    """
    Return True if each str in list_expected_strs is in list_actual_strs
    """
    return all(elem in list_actual_strs for elem in list_expected_strs)
