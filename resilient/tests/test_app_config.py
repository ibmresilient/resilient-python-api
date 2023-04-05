#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import os
import sys

import pytest
from tests.shared_mock_data.mock_plugins.mock_plugins import MyMockPlugin

from resilient import constants
from resilient.app_config import AppConfigManager, ProtectedSecretsManager


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY3_VERSION, reason="requires python3.6 or higher")
def test_protected_secrets_manager(fx_write_protected_secrets, fx_reset_environmental_variables):
    os.environ[constants.ENV_VAR_APP_HOST_CONTAINER] = "1"
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")
    psm = ProtectedSecretsManager(path_secrets_dir=path_secrets_dir, path_jwk_file=path_jwk_file)

    key = psm.get("$API_KEY")
    nothing = psm.get("$DOESNT_EXIST")

    assert key == "JbkOxTInUg1aIRGxXI8zOG1A25opU39lDKP1_0rfeVQ"
    assert nothing is None

def test_protected_secrets_manager_PY27(fx_reset_environmental_variables):
    os.environ["UNPROTECTED_API_KEY"] = "passw0rd"
    psm = ProtectedSecretsManager()

    key = psm.get("$UNPROTECTED_API_KEY")

    assert key == "passw0rd"

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
                    "password": "^secret"
                }
            }
        }
    }

    acm = AppConfigManager(original_dict, pam_plugin_type=MyMockPlugin)

    assert acm.get("b") == "MOCK"
    assert acm.get("nested").get("nested").get("nested").get("password") == "MOCK"
    assert acm["d"]["a"] == None

    os.environ["IN_ENV"] = "FOUND"
    assert acm["d"]["a"] == "FOUND"
