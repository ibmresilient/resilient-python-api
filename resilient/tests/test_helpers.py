#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging
import os
import sys

import pytest
from resilient import constants, helpers, app_config

if sys.version_info.major >= 3:
    # Handle PY 3 specific imports
    from jwcrypto.jwk import JWK


def test_str_to_bool():
    assert helpers.str_to_bool("True") is True
    assert helpers.str_to_bool("true") is True
    assert helpers.str_to_bool("1") is True
    assert helpers.str_to_bool("YeS") is True
    assert helpers.str_to_bool("ON") is True
    assert helpers.str_to_bool("2") is False
    assert helpers.str_to_bool(1) is True
    assert helpers.str_to_bool(0) is False
    assert helpers.str_to_bool("0") is False
    assert helpers.str_to_bool(None) is False


def test_is_env_proxies_set(fx_add_proxy_env_var):
    assert helpers.is_env_proxies_set() is True


def test_is_env_proxies_not_set():
    assert helpers.is_env_proxies_set() is False


def test_unquote_str():
    assert helpers.unquote_str("""%C2%B1%21%40%23%24%25%5E%26%2A%28%29_%2B""") == """±!@#$%^&*()_+"""
    assert helpers.unquote_str("""mockusername""") == """mockusername"""
    assert helpers.unquote_str("""mockpw1234567890%21%40%23%24%25%5E%26%2A%28%29-%2B_%3D%5B%5D%7B%3B%27%5C%7D%3A%22%7C/.%2C%3C%3E%3F%60%7E""") == """mockpw1234567890!@#$%^&*()-+_=[]{;'\}:"|/.,<>?`~"""
    assert helpers.unquote_str("") == ""
    assert helpers.unquote_str(None) == ""


def test_get_and_parse_proxy_env_var_not_set():
    assert helpers.get_and_parse_proxy_env_var() == {}


def test_get_and_parse_proxy_env_var(fx_add_proxy_env_var):
    proxy_details = helpers.get_and_parse_proxy_env_var()
    assert proxy_details["scheme"] == "http"
    assert proxy_details["hostname"] == "192.168.0.5"
    assert proxy_details["port"] == 3128
    assert proxy_details["username"] == ""
    assert proxy_details["password"] == ""


def test_get_and_parse_proxy_env_var_with_user(fx_add_proxy_env_var_with_user):
    proxy_details = helpers.get_and_parse_proxy_env_var()
    assert proxy_details["scheme"] == "http"
    assert proxy_details["hostname"] == "192.168.0.5"
    assert proxy_details["port"] == 3128
    assert proxy_details["username"] == "mockusername"
    assert proxy_details["password"] == """mockpw1234567890!@@@@#$%^&*()-+_=[]{;\'\\}:"/|,<>?`~"""


def test_is_in_no_proxy(fx_add_proxy_env_var):
    assert helpers.is_in_no_proxy("subdomain.example.com") is True
    assert helpers.is_in_no_proxy("192.168.1.5") is True
    assert helpers.is_in_no_proxy("domain.not.in.com") is False
    assert helpers.is_in_no_proxy("") is False
    assert helpers.is_in_no_proxy(None) is False


def test_no_proxy_is_not_set():
    assert helpers.is_in_no_proxy("subdomain.example.com") is False
    assert helpers.is_in_no_proxy("192.168.1.5") is False
    assert helpers.is_in_no_proxy("domain.not.in.com") is False
    assert helpers.is_in_no_proxy("") is False
    assert helpers.is_in_no_proxy(None) is False


def test_remove_tag():

    mock_res_obj = {
        "tags": [{"tag_handle": "fn_tag_test", "value": None}],
        "functions": [
            {"export_key": "fn_tag_test_function", "tags": [{'tag_handle': 'fn_tag_test', 'value': None}]}
        ],
        "workflows": {
            "nested_2": [{"export_key": "fn_tag_test_function", "tags": [{'tag_handle': 'fn_tag_test', 'value': None}]}]
        }
    }

    new_res_obj = helpers.remove_tag(mock_res_obj)

    assert new_res_obj.get("tags") == []
    assert new_res_obj.get("functions", [])[0].get("tags") == []
    assert new_res_obj.get("workflows", []).get("nested_2")[0].get("tags") == []


def test_is_running_in_app_host(fx_reset_environmental_variables):
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    assert helpers.is_running_in_app_host() is True


def test_is_not_running_in_app_host(caplog, fx_reset_environmental_variables):
    if constants.ENV_VAR_APP_HOST_CONTAINER in os.environ:
        del os.environ[constants.ENV_VAR_APP_HOST_CONTAINER]
    caplog.set_level(logging.DEBUG)
    assert helpers.is_running_in_app_host() is False
    assert "Not running in an App Host environment" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_protected_secret_exists(fx_write_protected_secrets, fx_reset_environmental_variables):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"

    assert helpers.protected_secret_exists("API_KEY", path_secrets_dir, path_jwk_file) is True
    assert helpers.protected_secret_exists("API_KEY", "invalid_path", path_jwk_file) is False
    assert helpers.protected_secret_exists("INVALID_SECRET_NAME", path_secrets_dir, path_jwk_file) is False
    assert helpers.protected_secret_exists("API_KEY", path_secrets_dir, "invalid_path") is False


@pytest.mark.skipif(sys.version_info >= constants.MIN_SUPPORTED_PY3_VERSION, reason="only run this test in Python 2.7")
def test_protected_secret_exists_unsupported_python_version(fx_reset_environmental_variables, caplog):

    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    assert helpers.protected_secret_exists("API_KEY", "mock_path", "mock_path") is False
    assert "Protected secrets are only supported for Python >= 3" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_protected_secret_exists_env_var_not_set(fx_write_protected_secrets, fx_reset_environmental_variables):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    if constants.ENV_VAR_APP_HOST_CONTAINER in os.environ:
        del os.environ[constants.ENV_VAR_APP_HOST_CONTAINER]
    assert helpers.protected_secret_exists("API_KEY", path_secrets_dir, path_jwk_file) is False


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_protected_secrets_keys(fx_write_protected_secrets, caplog, fx_reset_environmental_variables):
    path_secrets_dir = fx_write_protected_secrets

    expected_list = {"API_KEY", "EMAIL", "EMPTY", "PASSWORD", "PASSWORD_WITH_SPECIAL_CHARS", "URL"}
    keys_list = helpers.get_protected_secrets_keys(path_secrets_dir)

    assert isinstance(keys_list, set)
    assert expected_list == keys_list

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_protected_secret(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    token, key = helpers.get_protected_secret_token_and_key("API_KEY", path_secrets_dir, path_jwk_file)
    assert token and key

    assert helpers.decrypt_protected_secret(token, key, "API_KEY") == "JbkOxTInUg1aIRGxXI8zOG1A25opU39lDKP1_0rfeVQ"


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_protected_secret_empty_file(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    assert helpers.get_protected_secret_token_and_key("EMPTY", path_secrets_dir, path_jwk_file) is None
    assert "File for protected secret 'EMPTY' is empty or corrupt" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_protected_secret_wrong_key(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key_unused.jwk")

    token, key = helpers.get_protected_secret_token_and_key("API_KEY", path_secrets_dir, path_jwk_file)

    assert helpers.decrypt_protected_secret(token, key, "API_KEY") is None
    assert "Could not decrypt the secret. Invalid key used to decrypt the protected secret 'API_KEY'." in caplog.text


@pytest.mark.skipif(sys.version_info >= constants.MIN_SUPPORTED_PY3_VERSION, reason="only run this test in Python 2.7")
def test_get_protected_secret_unsupported_python_version(caplog):

    assert helpers.get_protected_secret_token_and_key("API_KEY", "mock_path", "mock_path") is None
    assert "Protected secrets are only supported for Python >= 3" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_jwk(fx_write_protected_secrets):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    jwk = helpers.get_jwk(path_jwk_file)
    in_json = jwk.export(as_dict=True)

    assert isinstance(jwk, JWK)
    assert in_json.get("k") == "W4VMVYqZg-xGiDTGjFFwRvbzf098AskheVdZPbpiYvE"


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_jwk_no_key(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, "EMPTY")

    assert helpers.get_jwk(path_jwk_file) is None
    assert "JWK JSON file at '{0}' is corrupt.".format(path_jwk_file) in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_get_jwk_invalid_file_path(fx_write_protected_secrets, caplog):
    assert helpers.get_jwk("invalid_path") is None
    assert "Could not find JWK at 'invalid_path' or you do not have the correct permissions." in caplog.text


def test_get_config_from_env(fx_reset_environmental_variables):
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    assert helpers.get_config_from_env(constants.ENV_VAR_APP_HOST_CONTAINER) == "1"
    assert helpers.get_config_from_env("invalid_env_var") is None


def test_load_pam_plugin_success_builtin():
    plugin_name = "Keyring"
    plugin = helpers.load_pam_plugin(plugin_name)

    assert plugin.__name__ == "Keyring"

def test_get_pam_type_name(fx_reset_environmental_variables, fx_write_protected_secrets):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")
    protected_secrets_manager = app_config.ProtectedSecretsManager(path_secrets_dir, path_jwk_file)

    opts = {"pam_type": None}
    assert helpers.get_pam_type_name(opts, protected_secrets_manager) == None

    opts = {"pam_type": "HashiCorpVault_Custom"}
    assert helpers.get_pam_type_name(opts, protected_secrets_manager) == "HashiCorpVault_Custom"

    os.environ["MY_PAM"] = "Keyring"
    opts = {"pam_type": "$MY_PAM"}
    assert helpers.get_pam_type_name(opts, protected_secrets_manager) == "Keyring"

    os.environ["PAM_TYPE"] = "HigherPrecedence"
    opts = {"pam_type": "LowerPrecedence"}
    assert helpers.get_pam_type_name(opts, protected_secrets_manager) == "HigherPrecedence"
