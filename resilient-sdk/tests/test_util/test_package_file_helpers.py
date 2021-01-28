#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import shutil
import json
import io
import pytest
from setuptools import sandbox as use_setuptools
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.sdk_exception import SDKException
from tests.shared_mock_data import mock_paths


def test_get_setup_callable():
    # Test callable section returned correctly.
    # Read the mock setup.py content.
    setup_content = sdk_helpers.read_file(mock_paths.MOCK_SETUP_PY)
    setup_callable = package_helpers.get_setup_callable(setup_content)
    # Read the mocked callable from processed setup.py
    with io.open(mock_paths.MOCK_SETUP_CALLABLE, mode="rt", encoding="utf-8") as the_file:
        mock_setup_callable = the_file.read()
    assert mock_setup_callable == setup_callable


def test_parse_setup_py():
    attributes_wanted = ["name", "version", "author", "long_description"]
    setup_attributes = package_helpers.parse_setup_py(mock_paths.MOCK_SETUP_PY, attributes_wanted)

    assert setup_attributes.get("name") == "fn_main_mock_integration"
    assert setup_attributes.get("version") == "1.2.3"
    assert setup_attributes.get("author") == "John છ જ ઝ ઞ ટ ઠ Smith"
    assert setup_attributes.get("long_description") == """Lorem ipsum dolor sit amet, tortor volutpat scelerisque facilisis vivamus eget pretium. Vestibulum turpis. Sed donec, nisl dolor ut elementum, turpis nulla elementum, pellentesque at nostra in et eget praesent. Nulla numquam volutpat sit, class quisque ultricies mollit nec, ullamcorper urna, amet eu magnis a sit nec. Ut urna massa non, purus donec mauris libero quisque quis, ઘ ઙ ચ છ જ ઝ ઞ libero purus eget donec at lacus, pretium a sollicitudin convallis erat eros, tristique eu aliquam."""


def test_get_dependency_from_install_requires():
    setup_attributes = package_helpers.parse_setup_py(mock_paths.MOCK_SETUP_PY, ["install_requires"])
    install_requires_str = setup_attributes.get("install_requires")
    res_circuits_dep_str = package_helpers.get_dependency_from_install_requires(install_requires_str, "resilient_circuits")

    assert res_circuits_dep_str == "resilient_circuits>=30.0.0"


def test_load_customize_py_module(fx_mk_temp_dir):
    path_customize_py = os.path.join(mock_paths.TEST_TEMP_DIR, "customize.py")
    shutil.copy(mock_paths.MOCK_CUSTOMIZE_PY, path_customize_py)

    loaded_customize_py = package_helpers.load_customize_py_module(path_customize_py)
    codegen_params = loaded_customize_py.codegen_reload_data()
    package_name = codegen_params.get("package")

    assert package_name == "fn_main_mock_integration"


def test_load_customize_py_module_with_resilient_circuits_dep(fx_mk_temp_dir):
    path_customize_py = os.path.join(mock_paths.TEST_TEMP_DIR, "customize.py")
    shutil.copy(mock_paths.MOCK_OLD_CUSTOMIZE_PY, path_customize_py)

    loaded_customize_py = package_helpers.load_customize_py_module(path_customize_py)
    codegen_params = loaded_customize_py.codegen_reload_data()
    package_name = codegen_params.get("package")

    assert package_name == "fn_service_now"


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


def test_get_icon():
    pass
    # TODO: add better mock data to test these
    # path_extension_logo = os.path.join(path_fn_mock_integration, "icons", "extension_logo.png")
    # path_company_logo = os.path.join(path_fn_mock_integration, "icons", "company_logo.png")

    # path_to_corrupt_jpg_icon = os.path.join(path_fn_mock_integration, "icons", "mock_corrupt_icon.jpg")
    # path_to_corrupt_png_icon = os.path.join(path_fn_mock_integration, "icons", "mock_corrupt_icon.png")

    # # Test getting extension_logo
    # extension_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_extension_logo, 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
    # self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

    # # Test getting default extension_logo
    # extension_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), "", 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
    # self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

    # # Test getting company_logo
    # company_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), path_company_logo, 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
    # self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

    # # Test getting default company_logo
    # company_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), "", 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
    # self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

    # # Test invalid paths
    # with self.assertRaisesRegex(OSError, "Could not find valid icon file. Looked at two locations:"):
    #     self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), "", 200, 72, "")

    # # Test not .png
    # with self.assertRaisesRegex(ExtException, ".jpg is not a supported icon file type. Icon file must be .png"):
    #     self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_to_corrupt_jpg_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)

    # # Test corrupt .png
    # with self.assertRaisesRegex(ExtException, "Icon file corrupt"):
    #     self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_to_corrupt_png_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)

    # # Test invalid resolution
    # with self.assertRaisesRegex(ExtException, "Resolution must be 10x10"):
    #     self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_extension_logo, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)


def test_add_tag():
    mock_list_objs = [
        {"key1": "obj1"},
        {"key2": "obj2"},
    ]

    tagged_objs = package_helpers.add_tag("mock_tag", mock_list_objs)
    tags = tagged_objs[0].get("tags")[0]
    assert tags["tag_handle"] is "mock_tag"
    assert tags["value"] is None


def test_add_tag_to_import_definition():
    # TODO: add better mock data to test these
    tag_name = "mock_tag_name"
    import_def = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    tagged_import_def = package_helpers.add_tag_to_import_definition(tag_name, package_helpers.SUPPORTED_RES_OBJ_NAMES, import_def)


def test_create_extension_display_name(fx_copy_fn_main_mock_integration):

    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    path_apiky_permissions_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
    output_dir = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_DIST_DIR)

    use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

    path_app_zip = package_helpers.create_extension(path_setup_py_file, path_apiky_permissions_file, output_dir)
    app_json = json.loads(sdk_helpers.read_zip_file(path_app_zip, "app.json"))

    assert app_json.get("display_name") == "Main Mock Integration"


def test_create_extension_image_hash(fx_copy_fn_main_mock_integration):

    mock_image_hash = "dd2a1678b6e0fd1d1a1313f78785fd0c4fad0565ac9008778bdb3b00bdff4420"

    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    path_apiky_permissions_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
    output_dir = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_DIST_DIR)

    use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

    path_app_zip = package_helpers.create_extension(path_setup_py_file, path_apiky_permissions_file, output_dir, image_hash=mock_image_hash)
    app_json = json.loads(sdk_helpers.read_zip_file(path_app_zip, "app.json"))

    assert app_json.get("current_installation", {}).get("executables", [])[0].get("image", "") == "ibmresilient/fn_main_mock_integration@sha256:dd2a1678b6e0fd1d1a1313f78785fd0c4fad0565ac9008778bdb3b00bdff4420"


def test_create_extension_invalid_image_hash(fx_copy_fn_main_mock_integration):

    mock_image_hash = "xxx"

    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    path_apiky_permissions_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
    output_dir = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_DIST_DIR)

    use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

    with pytest.raises(SDKException, match=r"image_hash 'xxx' is not a valid SHA256 hash\nIt must be a valid hexadecimal and 64 characters long"):
        package_helpers.create_extension(path_setup_py_file, path_apiky_permissions_file, output_dir, image_hash=mock_image_hash)
