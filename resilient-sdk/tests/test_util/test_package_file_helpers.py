#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import os
import shutil
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import helpers as sdk_helpers
from tests.shared_mock_data import mock_paths


def test_is_setup_attribute():
    assert package_helpers._is_setup_attribute("long_description='abc123'") is True
    assert package_helpers._is_setup_attribute("'abc123'") is False
    assert package_helpers._is_setup_attribute("#long_description='abc123'") is True
    assert package_helpers._is_setup_attribute("#long_description='abcઘ ઙ ચ છ જ ઝ ઞ123'") is True


def test_parse_setup_attribute():
    setup_py_lines = sdk_helpers.read_file(mock_paths.MOCK_SETUP_PY_LINES)
    setup_py_lines = [file_line.strip() for file_line in setup_py_lines]

    name = package_helpers._parse_setup_attribute(mock_paths.MOCK_SETUP_PY_LINES, setup_py_lines, "name")
    version = package_helpers._parse_setup_attribute(mock_paths.MOCK_SETUP_PY_LINES, setup_py_lines, "version")
    author = package_helpers._parse_setup_attribute(mock_paths.MOCK_SETUP_PY_LINES, setup_py_lines, "author")
    long_description = package_helpers._parse_setup_attribute(mock_paths.MOCK_SETUP_PY_LINES, setup_py_lines, "long_description")

    assert name == "fn_main_mock_integration"
    assert version == "1.2.3"
    assert author == u"John છ જ ઝ ઞ ટ ઠ Smith"
    assert long_description == u"""Lorem ipsum dolor sit amet, tortor volutpat scelerisque facilisis vivamus eget pretium. Vestibulum turpis. Sed donec, nisl dolor ut elementum, turpis nulla elementum, pellentesque at nostra in et eget praesent. Nulla numquam volutpat sit, class quisque ultricies mollit nec, ullamcorper urna, amet eu magnis a sit nec. Ut urna massa non, purus donec mauris libero quisque quis, ઘ ઙ ચ છ જ ઝ ઞ libero purus eget donec at lacus, pretium a sollicitudin convallis erat eros, tristique eu aliquam"""


def test_parse_setup_py():
    attributes_wanted = ["name", "version", "author", "long_description"]
    setup_attributes = package_helpers.parse_setup_py(mock_paths.MOCK_SETUP_PY, attributes_wanted)

    assert setup_attributes.get("name") == "fn_main_mock_integration"
    assert setup_attributes.get("version") == "1.2.3"
    assert setup_attributes.get("author") == u"John છ જ ઝ ઞ ટ ઠ Smith"
    assert setup_attributes.get("long_description") == u"""Lorem ipsum dolor sit amet, tortor volutpat scelerisque facilisis vivamus eget pretium. Vestibulum turpis. Sed donec, nisl dolor ut elementum, turpis nulla elementum, pellentesque at nostra in et eget praesent. Nulla numquam volutpat sit, class quisque ultricies mollit nec, ullamcorper urna, amet eu magnis a sit nec. Ut urna massa non, purus donec mauris libero quisque quis, ઘ ઙ ચ છ જ ઝ ઞ libero purus eget donec at lacus, pretium a sollicitudin convallis erat eros, tristique eu aliquam"""


def test_get_dependency_from_install_requires_str():
    setup_attributes = package_helpers.parse_setup_py(mock_paths.MOCK_SETUP_PY, ["install_requires"])
    install_requires_str = setup_attributes.get("install_requires")
    res_circuits_dep_str = package_helpers.get_dependency_from_install_requires_str(install_requires_str, "resilient_circuits")

    assert res_circuits_dep_str == "resilient_circuits>=30.0.0"


def test_load_customize_py_module(fx_mk_temp_dir):
    path_customize_py = os.path.join(mock_paths.TEST_TEMP_DIR, "customize.py")
    shutil.copy(mock_paths.MOCK_CUSTOMIZE_PY, path_customize_py)

    loaded_customize_py = package_helpers.load_customize_py_module(path_customize_py)
    codegen_params = loaded_customize_py.codegen_reload_data()
    package_name = codegen_params.get("package")

    assert package_name == "fn_main_mock_integration"


def test_get_import_definition_from_customize_py():
    import_def = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    functions = import_def.get("functions")
    fn = next(x for x in functions if x["export_key"] == "mock_function_one")
    fn_description = fn.get("description")["content"]

    assert isinstance(import_def, dict)
    assert fn_description == u"A mock description of mock_function_one with unicode:  ล ฦ ว ศ ษ ส ห ฬ อ"


def test_get_configs_from_config_py():
    config_str, mock_configs = package_helpers.get_configs_from_config_py(mock_paths.MOCK_CONFIG_PY)

    username = next(x for x in mock_configs if x["name"] == "username")
    unicode_entry = next(x for x in mock_configs if x["name"] == "unicode_entry")
    password = next(x for x in mock_configs if x["name"] == "password")

    assert config_str == u"""[fn_main_mock_integration]
username = <<enter_user_email_here>>
api_Key=dfghjFGYuy4567890nbvcghj
password = GJ^&*(';lkjhgfd567&*()_)

# Some random comments here
# and here

config_option=True

[other_section]
unicode_entry = ઘ ઙ ચ છ જ ઝ ઞ
"""

    assert username["name"] == "username"
    assert username["placeholder"] == "<<enter_user_email_here>>"
    assert username["section_name"] == "fn_main_mock_integration"
    assert password["placeholder"] == "GJ^&*(';lkjhgfd567&*()_)"
    assert unicode_entry["section_name"] == "other_section"
    assert unicode_entry["placeholder"] == u"ઘ ઙ ચ છ જ ઝ ઞ"
