#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import os
import sys

import pytest
from mock import patch
from tests.shared_mock_data.mock_plugins.mock_plugins import (MyBadMockPlugin,
                                                              MyMockPlugin)

from resilient import constants
from resilient.app_config import AppConfigManager, ProtectedSecretsManager

MOCK_API_KEY_VALUE = "JbkOxTInUg1aIRGxXI8zOG1A25opU39lDKP1_0rfeVQ"

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_protected_secrets_manager(fx_write_protected_secrets, fx_reset_environmental_variables):
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")
    psm = ProtectedSecretsManager(path_secrets_dir=path_secrets_dir, path_jwk_file=path_jwk_file)

    key = psm.get("$API_KEY")
    nothing = psm.get("$DOESNT_EXIST")

    assert key == MOCK_API_KEY_VALUE
    assert nothing is None

def test_protected_secrets_manager_PY27(fx_reset_environmental_variables):
    os.environ["UNPROTECTED_API_KEY"] = "passw0rd"
    os.environ["UNPROTECTED_SECRET_WITH_BRACKETS"] = "A[xyz)e}K,/MabS1}:NbJ$("
    psm = ProtectedSecretsManager()

    key = psm.get("$UNPROTECTED_API_KEY")
    key2 = psm.get("$UNPROTECTED_SECRET_WITH_BRACKETS")

    assert key == "passw0rd"
    assert key2 == "A[xyz)e}K,/MabS1}:NbJ$("

def test_app_config_manager_no_plugin():
    original_dict = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": {
            "a": 1,
            "b": 2
        },
        "nested": {
            "nested": {
                "nested": {
                    "password": "^secret"
                }
            }
        }
    }

    acm = AppConfigManager(original_dict)

    assert isinstance(acm, dict)

    # AppConfigManager objects have to support many ways of attribute accessing
    # for backward compatbility with existing app.config usages
    assert acm["a"] == original_dict["a"]
    assert acm["b"] == original_dict["b"]
    assert acm["c"] == original_dict["c"]
    assert acm.get("a") == original_dict.get("a")
    assert acm.get("b") == original_dict.get("b")
    assert acm.get("c") == original_dict.get("c")
    assert acm.a == original_dict.get("a")
    assert acm.b == original_dict.get("b")
    assert acm.c == original_dict.get("c")
    assert isinstance(acm["d"], AppConfigManager)
    assert isinstance(acm["nested"]["nested"]["nested"], AppConfigManager)
    assert isinstance(acm.get("d"), AppConfigManager)
    assert isinstance(acm.get("nested").get("nested").get("nested"), AppConfigManager)

    assert acm.get("nested").get("nested").get("nested").get("password") == "^secret"

    assert acm._asdict() == acm
    assert acm._asdict().get("nested") == acm.nested

def test_app_config_manager_with_plugin():
    original_dict = {
        "a": 1,
        "b": "^top.level/secret/with_special.characters",
        "d": {
            "a": "$IN_ENV",
            "b": "^shhh"
        },
        "nested": {
            "nested": {
                "nested": {
                    "password": "^secret",
                    "password2": "^{secret1} and ^{secret1}"
                }
            }
        }
    }

    acm = AppConfigManager(original_dict, pam_plugin_type=MyMockPlugin)

    assert acm.get("b") == "MOCK"
    assert acm.get("nested").get("nested").get("nested").get("password") == "MOCK"
    assert acm.get("nested").get("nested").get("nested").get("password2") == "MOCK and MOCK"
    assert acm["d"]["a"] == "$IN_ENV"

    os.environ["IN_ENV"] = "FOUND"
    assert acm["d"]["a"] == "FOUND"

    # check that __repr__ is not substituting in the protected values
    assert "^secret" in repr(acm)
    assert "^{secret1} and ^{secret1}" in repr(acm)
    assert "MOCK" not in repr(acm)

@pytest.mark.parametrize("item, prefix, expected", [
    # basic, old usage
    ("^item in keyring", "^", "MOCK"),

    # nothing substituted
    ("nothing", "^", "nothing"),
    ("nothing", "^{", "nothing"),

    # mid-item substituting
    ("^{item}some {text} in $between ^{another item}", "^{", "MOCKsome {text} in $between MOCK"),
    ("text ^{thensomestuff}", "^{", "text MOCK")
])
def test_replace_secret_in_config_pam_plugin(item, prefix, expected):
    manager = MyMockPlugin()
    replaced = AppConfigManager.replace_secret_in_config(item, manager, prefix)

    assert replaced == expected

@pytest.mark.parametrize("item, prefix, secret, expected", [
    ("$SECRET", "$", "A[xyz)e}K,/MabS1}:NbJ$(}$", "A[xyz)e}K,/MabS1}:NbJ$(}$"),
    ("${SECRET}${SECRET_2}", "${", "A[xyz)e}K,/MabS1}:NbJ$(}${", "A[xyz)e}K,/MabS1}:NbJ$(}${2")
])
def test_replace_secret_in_config_protected_secret_env_only(item, prefix, secret, expected, fx_reset_environmental_variables, caplog):
    manager = ProtectedSecretsManager()
    os.environ["SECRET"] = secret
    os.environ["SECRET_2"] = "2"

    replaced = AppConfigManager.replace_secret_in_config(item, manager, prefix)

    assert replaced == expected
    assert "Failed to find" not in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_replace_secret_in_config_protected_secret(fx_write_protected_secrets, fx_reset_environmental_variables):
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")
    manager = ProtectedSecretsManager(path_secrets_dir=path_secrets_dir, path_jwk_file=path_jwk_file)

    # NOTE: couldn't parametrize this test because of the protected secrets directory
    # creation not playing well with the parametrized mark
    for item, prefix, expected in [
        ("$protected_secret", "$", "FOUND"),

        # nothing substituted
        ("no protected secret", "$", "no protected secret"),
        ("no protected secret", "${", "no protected secret"),

        # mid-item substitutions
        ("${item} with other stuff here", "${", "FOUND with other stuff here"),
        ("start ${item} end", "${", "start FOUND end"),
        ("start ${item} another ${API_KEY}", "${", "start FOUND another {0}".format(MOCK_API_KEY_VALUE))
    ]:
        with patch("resilient.app_config.helpers.get_config_from_env") as patch_env_get:
            patch_env_get.return_value = "FOUND"
            replaced = AppConfigManager.replace_secret_in_config(item, manager, prefix)

            assert replaced == expected

def test_app_config_manager_bad_plugin():
    with pytest.raises(ValueError) as captured_err:
        AppConfigManager({}, MyBadMockPlugin)

    assert "'pam_plugin_type' must be a subclass of 'PAMPluginInterface'" in str(captured_err)
