#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

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
