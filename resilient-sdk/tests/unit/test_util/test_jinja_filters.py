#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from jinja2 import Environment
from resilient_sdk.util.jinja2_filters import add_filters_to_jinja_env, JINJA_FILTERS, _filter_base64, _filter_camel


def mock_setup_jinja_env():
    return Environment()


def test_filter_base64():
    mock_text = u"convert ᠭ ᠮ ᠯ me to base64"

    filtered_text = _filter_base64(mock_text)

    assert filtered_text == "ImNvbnZlcnQgXHUxODJkIFx1MTgyZSBcdTE4MmYgbWUgdG8gYmFzZTY0Ig==\n"


def test_filter_camel():
    mock_text = "Please#ReTurn_++Pla1n Camel Case"

    filtered_text = _filter_camel(mock_text)

    assert filtered_text == u"PleaseReturnPla1NCamelCase"


def test_add_filters_to_jinja_env():
    jinja_env = mock_setup_jinja_env()

    add_filters_to_jinja_env(jinja_env)

    assert all(elem in jinja_env.filters for elem in JINJA_FILTERS.keys()) is True
