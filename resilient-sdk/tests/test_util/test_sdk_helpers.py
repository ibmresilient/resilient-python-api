#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import stat
import re
import pytest
import jinja2
import sys
from resilient import SimpleClient
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from tests.shared_mock_data import mock_data, mock_paths


def test_get_resilient_client(fx_mk_temp_dir, fx_mk_app_config):
    res_client = sdk_helpers.get_resilient_client(path_config_file=fx_mk_app_config)
    assert isinstance(res_client, SimpleClient)


def test_setup_jinja_env():
    jinja_env = sdk_helpers.setup_jinja_env(mock_paths.TEST_TEMP_DIR)
    assert isinstance(jinja_env, jinja2.Environment)
    assert jinja_env.loader.package_path == mock_paths.TEST_TEMP_DIR


def test_read_write_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)
    assert os.path.isfile(temp_file)

    file_lines = sdk_helpers.read_file(temp_file)
    assert mock_data.mock_file_contents in file_lines

def test_read_json_file(fx_mk_temp_dir):
    export_data = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES)
    assert isinstance(export_data, dict)
    assert "functions" in export_data

def test_rename_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)

    sdk_helpers.rename_file(temp_file, "new_file_name.txt")
    path_renamed_file = os.path.join(mock_paths.TEST_TEMP_DIR, "new_file_name.txt")

    assert os.path.isfile(path_renamed_file) is True

def test_read_zip_file():
    file_lines = sdk_helpers.read_zip_file(mock_paths.MOCK_ZIP, "mock_file.txt")
    assert mock_data.mock_file_contents in file_lines

def test_is_valid_package_name():
    assert sdk_helpers.is_valid_package_name("fn_mock_integration") is True
    assert sdk_helpers.is_valid_package_name("fnmockintegration") is True
    assert sdk_helpers.is_valid_package_name("fn-mock-integration") is True
    assert sdk_helpers.is_valid_package_name("get") is False
    assert sdk_helpers.is_valid_package_name("$%&(#)@*$") is False
    assert sdk_helpers.is_valid_package_name("fn-ځ ڂ ڃ ڄ څ-integration") is False
    assert sdk_helpers.is_valid_package_name("fn-MockIntegration") is False

def test_is_valid_version_syntax():
    assert sdk_helpers.is_valid_version_syntax("1.0") is False
    assert sdk_helpers.is_valid_version_syntax("0") is False
    assert sdk_helpers.is_valid_version_syntax("1.0.0") is True
    assert sdk_helpers.is_valid_version_syntax("abc") is False


def test_is_valid_url():
    assert sdk_helpers.is_valid_url("www.example.com") is True
    assert sdk_helpers.is_valid_url("example.com") is True
    assert sdk_helpers.is_valid_url("http://www.example.com") is True
    assert sdk_helpers.is_valid_url("https://example.com") is True
    assert sdk_helpers.is_valid_url("https://www.example.com:8080") is True

    assert sdk_helpers.is_valid_url(None) is False
    assert sdk_helpers.is_valid_url("not a url") is False
    assert sdk_helpers.is_valid_url("https://www. example.com") is False


def test_does_url_contain():
    assert sdk_helpers.does_url_contain("http://www.example.com", "example") is True
    assert sdk_helpers.does_url_contain("not a url", "example") is False
    assert sdk_helpers.does_url_contain("http://www.example.com", "abc") is False


def test_generate_uuid_from_string():
    the_string, the_uuid = "fn_test_package", "7627eab9-8500-cf1d-380d-14a2c4364acf"
    the_generated_uuid = sdk_helpers.generate_uuid_from_string(the_string)
    assert the_generated_uuid == the_uuid


def test_has_permissions(fx_mk_temp_dir):
    temp_permissions_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_permissions.txt")
    sdk_helpers.write_file(temp_permissions_file, mock_data.mock_file_contents)

    # Set permissions to Read only
    os.chmod(temp_permissions_file, stat.S_IRUSR)

    with pytest.raises(SDKException, match=r"User does not have WRITE permissions"):
        sdk_helpers.has_permissions(os.W_OK, temp_permissions_file)

    # Set permissions to Write only
    os.chmod(temp_permissions_file, stat.S_IWUSR)

    with pytest.raises(SDKException, match=r"User does not have READ permissions"):
        sdk_helpers.has_permissions(os.R_OK, temp_permissions_file)


def test_validate_file_paths(fx_mk_temp_dir):
    non_exist_file = "/non_exits/path/non_exist_file.txt"
    with pytest.raises(SDKException, match=r"Could not find file: " + non_exist_file):
        sdk_helpers.validate_file_paths(None, non_exist_file)

    exists_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_existing_file.txt")
    sdk_helpers.write_file(exists_file, mock_data.mock_file_contents)

    sdk_helpers.validate_file_paths(None, exists_file)


def test_validate_dir_paths(fx_mk_temp_dir):
    non_exist_dir = "/non_exits/path/"
    with pytest.raises(SDKException, match=r"Could not find directory: " + non_exist_dir):
        sdk_helpers.validate_dir_paths(None, non_exist_dir)

    exists_dir = mock_paths.TEST_TEMP_DIR

    sdk_helpers.validate_dir_paths(None, exists_dir)


def test_read_local_exportfile():
    export_data = sdk_helpers.read_local_exportfile(mock_paths.MOCK_EXPORT_RES)
    assert isinstance(export_data, dict)
    assert "functions" in export_data

def test_read_local_exportfile_resz():
    export_data = sdk_helpers.read_local_exportfile(mock_paths.MOCK_EXPORT_RESZ)
    assert isinstance(export_data, dict)
    assert "functions" in export_data

def test_get_obj_from_list(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)
    export_data = sdk_helpers.get_from_export(org_export, functions=["mock_function_one", "mock_function_two"])

    all_functions = export_data.get("functions")
    got_functions = sdk_helpers.get_obj_from_list("export_key", all_functions)

    assert isinstance(got_functions, dict)
    assert "mock_function_one" in got_functions
    assert "mock_function_two" in got_functions

    # Test lambda condition
    got_functions = sdk_helpers.get_obj_from_list("export_key", all_functions, lambda o: True if o.get("export_key") == "mock_function_one" else False)
    assert "mock_function_one" in got_functions
    assert "mock_function_two" not in got_functions


def test_get_object_api_names(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)
    export_data = sdk_helpers.get_from_export(org_export,
                                              functions=["mock_function_one", "mock_function_two"])

    func_api_names = sdk_helpers.get_object_api_names("x_api_name", export_data.get("functions"))

    assert all(elem in ["mock_function_one", "mock_function_two"] for elem in func_api_names) is True


def test_get_res_obj(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    artifacts_wanted = ["mock_artifact_2", "mock_artifact_type_one"]
    artifacts = sdk_helpers.get_res_obj("incident_artifact_types", "programmatic_name", "Custom Artifact", artifacts_wanted, org_export)

    assert all(elem.get("x_api_name") in artifacts_wanted for elem in artifacts) is True


def test_get_res_obj_dict_in_wanted_list(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    wfs_wanted = [{"identifier": "name", "value": u"mock workflow  ล ฦ ว ศ ษ ส ห ฬ อ two"}]
    wfs = sdk_helpers.get_res_obj("workflows", "programmatic_name", "Workflow", wfs_wanted, org_export)

    assert len(wfs) == 1
    assert wfs[0].get("programmatic_name") == "mock_workflow_two"


def test_get_res_obj_exception(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    functions_wanted = ["mock_function_one", "fn_does_not_exist"]

    with pytest.raises(SDKException, match=r"Mock Display Name: 'fn_does_not_exist' not found in this export"):
        sdk_helpers.get_res_obj("functions", "export_key", "Mock Display Name", functions_wanted, org_export)


def test_get_message_destination_from_export(fx_mock_res_client):
    # TODO: Add test for all resilient objects...
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    export_data = sdk_helpers.get_from_export(org_export,
                                              message_destinations=["fn_main_mock_integration"])

    assert export_data.get("message_destinations")[0].get("name") == "fn_main_mock_integration"


@pytest.mark.parametrize("get_related_param",
                         [(True), (False)])
def test_get_related_objects_when_getting_from_export(fx_mock_res_client, get_related_param):

    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    export_data = sdk_helpers.get_from_export(org_export,
                                              message_destinations=["fn_main_mock_integration"],
                                              functions=["mock_function__three"],
                                              get_related_objects=get_related_param)

    assert export_data.get("message_destinations")[0].get("name") == "fn_main_mock_integration"

    if get_related_param:
        assert len(export_data.get("functions", [])) > 0
        assert any(elem.get("name") in ("mock_function_one", "mock_function_two") for elem in export_data.get("functions")) is True

    else:
        assert all(elem.get("name") in ("mock_function_one", "mock_function_two") for elem in export_data.get("functions")) is False


def test_minify_export(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    minifed_export = sdk_helpers.minify_export(org_export, functions=["mock_function_one"])
    minified_functions = minifed_export.get("functions")
    minified_fields = minifed_export.get("fields")
    minified_incident_types = minifed_export.get("incident_types")

    # Test it minified given function
    assert len(minified_functions) == 1
    assert minified_functions[0].get("export_key") == "mock_function_one"

    # Test it set a non-mentioned object to 'empty'
    assert minifed_export.get("phases") == []

    # Test it added the internal field
    assert len(minified_fields) == 1
    assert minified_fields[0].get("export_key") == "incident/internal_customizations_field"
    assert minified_fields[0].get("uuid") == "bfeec2d4-3770-11e8-ad39-4a0004044aa1"

    # Test it added the default incident type
    assert len(minified_incident_types) == 1
    assert minified_incident_types[0].get("export_key") == "Customization Packages (internal)"
    assert minified_incident_types[0].get("uuid") == "bfeec2d4-3770-11e8-ad39-4a0004044aa0"


def test_minify_export_default_keys_to_keep(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    minifed_export = sdk_helpers.minify_export(org_export)

    assert "export_date" in minifed_export
    assert "export_format_version" in minifed_export
    assert "id" in minifed_export
    assert "server_version" in minifed_export


def test_load_by_module():
    path_python_file = os.path.join(mock_paths.SHARED_MOCK_DATA_DIR, "mock_data.py")
    module_name = "mock_data"
    mock_data_module = sdk_helpers.load_py_module(path_python_file, module_name)

    assert mock_data_module.mock_loading_this_module == "yes you did!"


def test_rename_to_bak_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)

    sdk_helpers.rename_to_bak_file(temp_file)

    files_in_dir = os.listdir(mock_paths.TEST_TEMP_DIR)
    regex = re.compile(r'^mock_file\.txt-\d+\d+\d+\d+\d+\d+\d+\.bak$')
    matched_file_name = list(filter(regex.match, files_in_dir))[0]

    assert regex.match(matched_file_name)


def test_rename_to_bak_file_if_file_not_exist(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    path_to_backup = sdk_helpers.rename_to_bak_file(temp_file)
    assert temp_file == path_to_backup


def test_generate_anchor():
    anchor = sdk_helpers.generate_anchor(u"D מ ן נ ס עata Ta!@#$%^&*()__ble Utせ ぜ そ ぞ た だils: ✔✕✖✗✘✙✚✛ òDelete_Rowﻀ ﻁ ﻂ ﻃ ﻄ ﻅ ﻆ ﻇ ﻈ and 㐖 㐗 㐘 㐙 㐚 㐛 㐜 㐝")
    assert anchor == u"d-מ-ן-נ-ס-עata-ta__ble-utせ-ぜ-そ-ぞ-た-だils--òdelete_rowﻀ-ﻁ-ﻂ-ﻃ-ﻄ-ﻅ-ﻆ-ﻇ-ﻈ-and-㐖-㐗-㐘-㐙-㐚-㐛-㐜-㐝"


def test_simplify_string():
    assert "d-----ata-ta--ble-ut-----ils--delete-row---------and--------" == sdk_helpers.simplify_string("D מ ן נ ס עata Ta!@#$%^&*()__ble Utせ ぜ そ ぞ た だils: ✔✕✖✗✘✙✚✛ òDelete_Rowﻀ ﻁ ﻂ ﻃ ﻄ ﻅ ﻆ ﻇ ﻈ and 㐖 㐗 㐘 㐙 㐚 㐛 㐜 㐝")


def test_get_workflow_functions():
    # TODO: taken from docgen
    pass


def test_get_main_cmd(monkeypatch):
    mock_args = ["resilient-sdk", "codegen", "-p", "fn_mock_package"]
    monkeypatch.setattr(sys, "argv", mock_args)
    main_cmd = sdk_helpers.get_main_cmd()
    assert main_cmd == "codegen"


def test_get_timestamp():
    now = sdk_helpers.get_timestamp()
    assert re.match(r"\d\d\d\d\d\d\d\d\d\d\d\d\d\d", now)


def test_get_timestamp_from_timestamp():
    ts = sdk_helpers.get_timestamp(1579258053.728)
    assert ts == "20200117104733"


def test_str_to_bool():
    assert sdk_helpers.str_to_bool('True') is True
    assert sdk_helpers.str_to_bool('true') is True
    assert sdk_helpers.str_to_bool('YES') is True
    assert sdk_helpers.str_to_bool('truex') is False
    assert sdk_helpers.str_to_bool(1) is True
    assert sdk_helpers.str_to_bool(0) is False
    assert sdk_helpers.str_to_bool('0') is False
