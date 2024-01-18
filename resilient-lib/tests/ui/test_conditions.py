#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

from resilient_lib.ui import Field, Tab, SelectField
import uuid

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
    assert SelectField("user_id", OPTS).conditions.has_value() == {
        "field": "incident.user_id", "condition": "has_a_value"
    }
    assert SelectField("user_id", OPTS).conditions.equals("Default Group") == {
        "field": "incident.user_id", "condition": "equals", "value": "3"
    }
    assert SelectField("user_id", OPTS).conditions.has_one_of(["Default Group"]) == {
        "field": "incident.user_id", "condition": "in", "value": ["3"]
    }
    assert SelectField("user_id", OPTS).conditions.doesnt_have_one_of(["Default Group"]) == {
        "field": "incident.user_id", "condition": "not_in", "value": ["3"]
    }
    assert SelectField("user_id", OPTS).conditions.doesnt_equal("Default Group") == {
        "field": "incident.user_id", "condition": "not_equals", "value": "3"
    }
