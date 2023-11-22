#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import io
import json
import os
import shutil

import pytest
from mock import patch
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.sdk_exception import SDKException
from setuptools import sandbox as use_setuptools
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
    assert setup_attributes.get("not_existing") is None


def test_get_package_name(fx_copy_fn_main_mock_integration):
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]
    package_name = package_helpers.get_package_name(path_fn_main_mock_integration)

    assert package_name == "fn_main_mock_integration"


def test_get_package_name_invalid_path():
    with pytest.raises(SDKException, match=r"ERROR: Could not find file: mock-path/setup.py"):
        package_helpers.get_package_name("mock-path")


def test_get_dependency_from_install_requires():
    setup_attributes = package_helpers.parse_setup_py(mock_paths.MOCK_SETUP_PY, [constants.SETUP_PY_INSTALL_REQ_NAME])
    install_requires_str = setup_attributes.get(constants.SETUP_PY_INSTALL_REQ_NAME)
    res_circuits_dep_str = package_helpers.get_dependency_from_install_requires(install_requires_str, "resilient_circuits")
    assert res_circuits_dep_str == "resilient_circuits>=30.0.0"

    # make sure works with "resiilent-circuits" too even if the install_requires specifies "_"
    res_circuits_dep_str = package_helpers.get_dependency_from_install_requires(install_requires_str, "resilient-circuits")
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


def test_create_extension_minimum_resilient_version(fx_copy_fn_main_mock_integration):

    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    path_apiky_permissions_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
    output_dir = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_DIST_DIR)

    use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

    path_app_zip = package_helpers.create_extension(path_setup_py_file, path_apiky_permissions_file, output_dir)
    app_json = json.loads(sdk_helpers.read_zip_file(path_app_zip, "app.json"))

    assert app_json.get("minimum_resilient_version", {}) == {'build_number': 6783, 'major': 41, 'minor': 0, 'version': '41.0.6783'}

def test_create_extension_minimum_resilient_version_new_style(fx_copy_fn_main_mock_integration_w_playbooks):

    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration_w_playbooks[1]

    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    path_apiky_permissions_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
    output_dir = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_DIST_DIR)

    use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

    path_app_zip = package_helpers.create_extension(path_setup_py_file, path_apiky_permissions_file, output_dir)
    app_json = json.loads(sdk_helpers.read_zip_file(path_app_zip, "app.json"))

    assert app_json.get("minimum_resilient_version", {}) == {'build_number': 5678, 'v': 51, 'r': 2, 'm': 3, 'f': 4, 'major': 0, 'minor': 0, 'version': '51.2.3.4.5678'}

def test_get_required_python_version():

    parsed_version = package_helpers.get_required_python_version(">=3")
    assert parsed_version == (3, 0, 0)
    
    parsed_version = package_helpers.get_required_python_version(">=2.7")
    assert parsed_version == (2, 7, 0)

    with pytest.raises(SDKException):
        package_helpers.get_required_python_version("<4")

def test_check_package_installed():
    
    # positive case
    assert package_helpers.check_package_installed("resilient-sdk") is True

    # negative case
    assert package_helpers.check_package_installed("this-is-a-fake-package") is False

def test_color_output():

    mock_data_to_color = [
        ("COLOR this in GREEN for PASS", "PASS"),
        ("COLOR this in GREEN for DEBUG", "DEBUG"),
        ("COLOR this in RED for FAIL", "FAIL"),
        ("COLOR this in RED for CRITICAL", "CRITICAL"),
        ("COLOR this in YELLOW for WARNING", "WARNING"),
        ("COLOR this in NORMAL for INFO", "INFO")
    ]

    for s, level in mock_data_to_color:
        output = package_helpers.color_output(s, level)
        assert output.startswith(package_helpers.COLORS[level]) and output.endswith(package_helpers.COLORS["END"]) and s in output


def test_color_output_printing(caplog):
    mock_text = u"Mock printing this out ŏ Ő ő Œ œ Ŕ ŕ Ŗ"
    package_helpers.color_output(mock_text, constants.VALIDATE_LOG_LEVEL_INFO, do_print=True)

    assert mock_text in caplog.text


def test_color_diff_output():

    mock_diff_data_generator = (
        "--- fromfile\n",
        "+++ tofile\n",
        "\n",
        "@@ -1 +1 @@\n",
        "-test\n",
        "+Testing\n"
    )

    output = package_helpers.color_diff_output(mock_diff_data_generator)

    for i, line in enumerate(output):
        # for lines that are colored, check that they start with the right color
        # then check that the original start of the line is still there
        if i == 0:
            assert line.startswith(package_helpers.COLORS["RED"])
            assert line[len(package_helpers.COLORS["RED"]):].startswith("---" + package_helpers.COLORS["END"])
        elif i == 1:
            assert line.startswith(package_helpers.COLORS["GREEN"])
            assert line[len(package_helpers.COLORS["GREEN"]):].startswith("+++" + package_helpers.COLORS["END"])
        elif i == 4:
            assert line.startswith(package_helpers.COLORS["RED"])
            assert line[len(package_helpers.COLORS["RED"]):].startswith("-" + package_helpers.COLORS["END"])
        elif i == 5:
            assert line.startswith(package_helpers.COLORS["GREEN"])
            assert line[len(package_helpers.COLORS["GREEN"]):].startswith("+" + package_helpers.COLORS["END"])
        else:
            # lines that shouldn't get any color added
            assert line == mock_diff_data_generator[i]


def test_pass_parse_file_paths_from_readme():

    mock_passing_readme_data = ["# Header\n", "![this is a file](path.png)\n", 
                    "<!-- ![a commented out link](not.png) -->", "another markdown **line**\n"]

    result = package_helpers.parse_file_paths_from_readme(mock_passing_readme_data)

    assert "path.png" in result
    assert "not.png" not in result


    # and now check that it raises an SDKException when there's an invalid link
    mock_invalid_readme_data = ["# Header\n", "![this is not a link]\n"]

    with pytest.raises(SDKException):
        result = package_helpers.parse_file_paths_from_readme(mock_invalid_readme_data)


def test_parse_dockerfile():

    command_dict = package_helpers.parse_dockerfile(mock_paths.MOCK_DOCKERFILE_PATH)

    from_list = [constants.DOCKER_BASE_REPO]
    arg_list = [
        "APPLICATION=fn_main_mock_integration",
        "RESILIENT_CIRCUITS_VERSION=37",
        "PATH_RESILIENT_CIRCUITS=rescircuits",
        "APP_HOST_CONTAINER=1"
        ]
    env_list = [
        r"APP_HOST_CONTAINER=${APP_HOST_CONTAINER}",
        r"APP_CONFIG_FILE /etc/${PATH_RESILIENT_CIRCUITS}/app.config",
        r"APP_LOG_DIR /var/log/${PATH_RESILIENT_CIRCUITS}"
    ]
    user_list = ["0","1001"]
    run_list = [
        "pip install --upgrade pip",
        r'pip install "resilient-circuits>=${RESILIENT_CIRCUITS_VERSION}"',
        r"pip install /tmp/packages/${APPLICATION}-*.tar.gz",
        r"mkdir /etc/${PATH_RESILIENT_CIRCUITS}",
        "groupadd -g 1001 default && usermod -g 1001 default",
        r"mkdir /var/log/${PATH_RESILIENT_CIRCUITS} && \ ".strip(),
        r"mkdir /var/${PATH_RESILIENT_CIRCUITS}",
        r"mkdir /opt/${PATH_RESILIENT_CIRCUITS}"
        ]
    copy_list = ["./dist /tmp/packages",r"entrypoint.sh /opt/${PATH_RESILIENT_CIRCUITS}/entrypoint.sh"]
    entrypoint_list = ['[ "sh", "/opt/rescircuits/entrypoint.sh" ]']
    empty_list = [
        r"chgrp -R 1001 /var/log/${PATH_RESILIENT_CIRCUITS} && \ ".strip(),
        r"chmod -R g=u /var/log/${PATH_RESILIENT_CIRCUITS}"]
    
    assert command_dict[constants.DOCKER_COMMAND_DICT["from_command"]] == from_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["set_argument"]] == arg_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["set_env_var"]] == env_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["user"]] == user_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["run_command"]] == run_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["copy_command"]] == copy_list
    assert command_dict[constants.DOCKER_COMMAND_DICT["entrypoint"]] == entrypoint_list


def test_parse_dockerfile_unicode():
    with patch("resilient_sdk.util.sdk_helpers.read_file") as mock_lines:
        mock_lines.return_value = [
            "FROM unicode testing mock",
            "RUN ɐ ɑ ɒ ɓ ɔ ɕ",
            "يجري a command!",
            "TIBET ༀ ༁ ༂"
        ]
        command_dict = package_helpers.parse_dockerfile(mock_paths.MOCK_DOCKERFILE_PATH)

    assert command_dict["FROM"] == ["unicode testing mock"]
    assert command_dict["RUN"] == ["ɐ ɑ ɒ ɓ ɔ ɕ"]
    assert command_dict["يجري"] == ["a command!"]
    assert command_dict["TIBET"] == ["ༀ ༁ ༂"]


def test_color_lines_empty():
    assert not package_helpers.color_lines("WARNING", [])


def test_color_lines():
    colored_lines = package_helpers.color_lines("CRITICAL", [u"WARNING:", u"This is a mock Ķ ķ ĸ Ĺ ĺ Ļ ļ error"])
    assert colored_lines[0] == u"\x1b[91m\n------------------------\n\x1b[0m"
    assert colored_lines[1] == u"\x1b[91mWARNING:\x1b[0m"
    assert colored_lines[2] == u"\x1b[91mThis is a mock Ķ ķ ĸ Ĺ ĺ Ļ ļ error\x1b[0m"


def test_print_latest_version_warning(caplog):
    package_helpers.print_latest_version_warning("40.0.0", "41.0.0")
    msg = "WARNING:\n'40.0.0' is not the latest version of the resilient-sdk. \
'v41.0.0' is available on https://pypi.org/project/resilient-sdk/\n\n\
To update run:\n\t$ pip install -U resilient-sdk"
    assert msg in caplog.text

def test_get_export_from_zip():
    export_content = package_helpers.get_export_from_zip(mock_paths.MOCK_EXPORT_RESZ)

    assert export_content
    assert len(export_content["workflows"]) == 2 # just a simple check

def test_get_export_from_zip_not_found():
    with pytest.raises(SDKException):
        package_helpers.get_export_from_zip(mock_paths.MOCK_EXPORT_RES) # not a zip file

