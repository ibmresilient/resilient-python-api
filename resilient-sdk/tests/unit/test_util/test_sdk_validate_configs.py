#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import pytest
from resilient_sdk.util import package_file_helpers, sdk_validate_configs
from resilient_sdk.util.sdk_exception import SDKException
from tests.shared_mock_data.mock_paths import MOCK_SETUP_PY


def test_name_lambda():

    func = sdk_validate_configs.setup_py_attributes[0][1].get("fail_func", None)
    
    assert func is not None
    assert not func("test_name")
    assert not func("name_with_n0mb3rs")
    assert func("test_name_with invalid characters")

def test_display_name_lambda():

    func = sdk_validate_configs.setup_py_attributes[1][1].get("fail_func", None)
    
    assert func is not None
    assert not func("This is My Display Name")
    assert not func("This is My Display Name ส ห ฬ ")
    assert func("<<default display name>>")

def test_display_name_not_name_func():

    func = sdk_validate_configs.setup_py_attributes[2][1].get("fail_func", None)
    
    assert func is not None
    assert not func("Main Mock Integration", MOCK_SETUP_PY)
    assert func("fn_main_mock_integration", MOCK_SETUP_PY)

def test_no_display_name_not_name_func():

    func = sdk_validate_configs.setup_py_attributes[2][1].get("fail_func", None)
    
    assert func is not None
    assert not func("Main Mock Integration", MOCK_SETUP_PY)
    assert func("fn_main_mock_integration", MOCK_SETUP_PY)
    assert not func(None, MOCK_SETUP_PY)

def test_license_lambda():

    func = sdk_validate_configs.setup_py_attributes[3][1].get("fail_func", None)
    
    assert func is not None
    assert not func("MIT")
    assert func("<<default license>>")

def test_author_lambda():

    func = sdk_validate_configs.setup_py_attributes[5][1].get("fail_func", None)
    
    assert func is not None
    assert not func("IBM")
    assert func("<<default author>>")

def test_author_email_lambda():

    func = sdk_validate_configs.setup_py_attributes[6][1].get("fail_func", None)
    
    assert func is not None
    assert not func("ibm@ibm.com")
    assert not func("<<default email>>")
    assert func("example@example.com")

def test_description_lambda():

    func = sdk_validate_configs.setup_py_attributes[7][1].get("fail_func", None)

    assert func is not None
    assert not func("My Custom Function is well described")
    assert func("<<::CHANGE_ME::>>IBM SOAR app fn_test")

def test_long_description_lambda():

    func = sdk_validate_configs.setup_py_attributes[8][1].get("fail_func", None)

    assert func is not None
    assert not func("My Custom Function is well described. And the description is long.")
    assert func("<<::CHANGE_ME::>> to include app description and key features")

def test_install_requires_lambda():

    func = sdk_validate_configs.setup_py_attributes[9][1].get("fail_func", None)
    
    assert func is not None
    assert not func(['resilient_circuits>=30.0.0', 'boto3'])
    assert not func(['resilient-circuits>=30.0.0', 'fn-utilities'])
    assert func(["'only-this-package'"])

def test_install_requires_version_specifier_lambda():

    func = sdk_validate_configs.setup_py_attributes[10][1].get("fail_func", None)
    
    assert func is not None
    assert func(['resilient_circuits>=30.0.0', 'boto3'])
    assert not func(['resilient-circuits>=30.0.0', 'fn-utilities~=1.12'])
    assert func(["'only-this-package'"])

def test_python_requires_lambda():

    func = sdk_validate_configs.setup_py_attributes[11][1].get("fail_func", None)
    
    assert func is not None
    assert not func(">=3.6")
    assert func(">=2.0")
    assert func(">=0.0")
    with pytest.raises(SDKException):
        func("<2")
    with pytest.raises(SDKException):
        func("<=2.7")

def test_entry_points_lambda():

    func = sdk_validate_configs.setup_py_attributes[12][1].get("fail_func", None)
    
    assert func is not None
    assert not func(package_file_helpers.SUPPORTED_EP)
    assert func(["only_one_entry_point"])
