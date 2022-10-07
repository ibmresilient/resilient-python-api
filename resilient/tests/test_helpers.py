#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
from resilient import helpers


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


def test_protected_secret_exists(fx_write_protected_secrets):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    assert helpers.protected_secret_exists("API_KEY", path_secrets_dir, path_jwk_file) is True
    assert helpers.protected_secret_exists("API_KEY", "invalid_path", path_jwk_file) is False
    assert helpers.protected_secret_exists("INVALID_SECRET_NAME", path_secrets_dir, path_jwk_file) is False
    assert helpers.protected_secret_exists("API_KEY", path_secrets_dir, "invalid_path") is False


def test_get_protected_secret(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    assert helpers.get_protected_secret("API_KEY", path_secrets_dir, path_jwk_file) == "JbkOxTInUg1aIRGxXI8zOG1A25opU39lDKP1_0rfeVQ"


def test_get_protected_secret_empty_file(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    assert helpers.get_protected_secret("EMPTY", path_secrets_dir, path_jwk_file) is None
    assert "ERROR: File for protected secret 'EMPTY' is empty or corrupt" in caplog.text


def test_get_protected_secret_wrong_key(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key_unused.jwk")

    assert helpers.get_protected_secret("API_KEY", path_secrets_dir, path_jwk_file) is None
    assert "ERROR: Invalid key used to decrypt the protected secret 'API_KEY'." in caplog.text


def test_get_jwk(fx_write_protected_secrets):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, ".jwk", "key.jwk")

    assert helpers.get_jwk(path_jwk_file) == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def test_get_jwk_no_key(fx_write_protected_secrets, caplog):
    path_secrets_dir = fx_write_protected_secrets
    path_jwk_file = os.path.join(path_secrets_dir, "EMPTY")

    assert helpers.get_jwk(path_jwk_file) is None
    assert "JWK JSON file at '{0}' is corrupt or does not in include the required 'k' attribute.".format(path_jwk_file) in caplog.text


def test_get_jwk_invalid_file_path(fx_write_protected_secrets, caplog):
    assert helpers.get_jwk("invalid_path") is None
    assert "WARNING: Could not find JWK at 'invalid_path' or you do not have the correct permissions." in caplog.text
