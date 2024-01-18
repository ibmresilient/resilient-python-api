#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

import uuid

from mock import patch
from resilient_lib.ui import Field, SelectField, Tab

OPTS = {
    "host": "test.example.com",
    "api_key_id": "*****",
    "api_key_secret": "*****",
    "org": "Test Organization"
}

def test_can_initialize():
    assert Field("test").conditions is not None
    assert Field("test").conditions.has_value() is not None
    assert Field("test").conditions.equals("test") is not None

def test_conditions_added_to_dto():
    class TestTab(Tab):
        NAME = "test_tab"
        UUID = uuid.uuid4()
        SECTION = "fn_test"

        CONTAINS = [Field("test")]
        SHOW_IF = [Field("test").conditions.contains("value")]

    assert TestTab.as_dto()["show_if"] == TestTab.SHOW_IF


def test_select_field_conditions(fx_soar_adapter):
    """fx_soar_adapter required here for adapter which patches SOAR endpoints"""
    fake_field_name = "user_id"
    fake_label = "Default Group"
    fake_value = "3"

    assert SelectField(fake_field_name, OPTS).conditions.has_value() == {
        "field": "incident.{}".format(fake_field_name), "condition": "has_a_value"
    }
    assert SelectField(fake_field_name, OPTS).conditions.equals(fake_label) == {
        "field": "incident.{}".format(fake_field_name), "condition": "equals", "value": fake_value
    }
    assert SelectField(fake_field_name, OPTS).conditions.has_one_of([fake_label]) == {
        "field": "incident.{}".format(fake_field_name), "condition": "in", "value": [fake_value]
    }
    assert SelectField(fake_field_name, OPTS).conditions.doesnt_have_one_of([fake_label]) == {
        "field": "incident.{}".format(fake_field_name), "condition": "not_in", "value": [fake_value]
    }
    assert SelectField(fake_field_name, OPTS).conditions.doesnt_equal(fake_label) == {
        "field": "incident.{}".format(fake_field_name), "condition": "not_equals", "value": fake_value
    }
