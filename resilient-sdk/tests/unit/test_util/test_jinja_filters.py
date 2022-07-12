#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from jinja2 import Environment
from resilient_sdk.util import jinja2_filters


def mock_setup_jinja_env():
    return Environment()


def test_filter_base64():
    mock_text = u"convert ᠭ ᠮ ᠯ me to base64"

    filtered_text = jinja2_filters._filter_base64(mock_text)

    assert filtered_text == "ImNvbnZlcnQgXHUxODJkIFx1MTgyZSBcdTE4MmYgbWUgdG8gYmFzZTY0Ig==\n"


def test_filter_camel():
    mock_text = "Please#ReTurn_++Pla1n Camel Case"

    filtered_text = jinja2_filters._filter_camel(mock_text)

    assert filtered_text == u"PleaseReturnPla1NCamelCase"


def test_dot_py():
    mock_text = "validating setup.py"

    filtered_text = jinja2_filters._dot_py(mock_text)

    assert filtered_text == u"validating `setup.py`"


def test_scrub_ansi():
    mock_text = "\033[92msome green text\033[0m"

    filtered_text = jinja2_filters._scrub_ansi(mock_text)

    assert filtered_text == u"some green text"


def test_convert_to_code():
    mock_text = "'''pip install -U 'resilient-circuits''''"

    filtered_text = jinja2_filters._convert_to_code(mock_text)

    assert "```shell\n$ pip install -U \"resilient-circuits\"\n```" in filtered_text


def test_defaults_to_code():
    mock_text = "<<example url>>"

    filtered_text = jinja2_filters._defaults_to_code(mock_text)

    assert filtered_text == "`<<example url>>`"


def test_render_diff():
    mock_text = "\n\t\t--- from\n\t\t+++ to\n\t\t@@ -1 +1 @@\n\t\t-no\n\t\t+yes\n\t\t"

    filtered_text = jinja2_filters._render_diff(mock_text)

    assert "```diff\n--- from\n+++ to\n@@ -1 +1 @@\n-no\n+yes\n```" in filtered_text


def test_readable_time_from_timestamp():
    mock_timestamp = "20211118104506"

    converted_time = jinja2_filters._readable_time_from_timestamp(mock_timestamp)

    assert "2021/11/18 10:45:06" == converted_time


def test_add_filters_to_jinja_env():
    jinja_env = mock_setup_jinja_env()

    jinja2_filters.add_filters_to_jinja_env(jinja_env)

    assert all(elem in jinja_env.filters for elem in jinja2_filters.JINJA_FILTERS.keys()) is True
