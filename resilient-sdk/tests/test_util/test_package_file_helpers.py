#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

from resilient_sdk.util import package_file_helpers as package_helpers


def test_load_customize_py_module():
    # TODO
    # using old resilient-circuits
    # generate old customize.py using fn_mock_integration
    # save that in mock data
    # Read it in here and confirm we an call load_params function
    pass

# TODO: use this anywhere in tests we compare lists (instead of using for loop)
# self.assertTrue(all(elem in custom_incident_fields_details for elem in mock_data.mock_custom_incident_fields_details))