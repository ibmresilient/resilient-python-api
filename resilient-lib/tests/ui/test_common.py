#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

import json

from resilient_lib.ui import (Datatable, Field, Header, HTMLBlock, Section,
                              Tab, create_tab, update_summary_layout)

OPTS = {
    "host": "test.example.com",
    "api_key_id": "*****",
    "api_key_secret": "*****",
    "org": "Test Organization"
}

class MockTab(Tab):
    NAME = "test"
    UUID = "test"
    SECTION = "test"
    CONTAINS = [
        Datatable('test'),
        Field('test'),
        Section(
            element_list=[HTMLBlock("<h1>HTML Header</h1>"), Header("Built-in Header")],
            show_if=[Field("id").conditions.has_value()]
        )
    ]

    SHOW_IF = [Field('test').conditions.has_value()]

class TestSubmittedData(object):
    """
    Tests that payload submitted to the server contains proper tab information.
    """

    def test_create_tab(self, fx_soar_adapter):
        create_tab(MockTab, OPTS)

        payload = json.loads(fx_soar_adapter.request_history[-1].text)
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(payload.get('content')).get("fields"))

    def test_update_tab_disabled(self, fx_soar_adapter):
        create_tab(MockTab, OPTS)

        # assert that PUT was called and correct payload present
        assert fx_soar_adapter.call_count == 5


    def test_update_tab_enabled(self, fx_soar_adapter):
        create_tab(MockTab, OPTS, update_existing=True)

        payload = json.loads(fx_soar_adapter.request_history[-1].text)
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(payload.get('content')).get("fields"))

    def test_conditions_sent(self, fx_soar_adapter):
        create_tab(MockTab, OPTS, update_existing=True)

        assert fx_soar_adapter.call_count == 5

        assert str(fx_soar_adapter.request_history[-1]) == "PUT https://test.example.com:443/rest/orgs/201/layouts/4"

        payload = json.loads(fx_soar_adapter.request_history[-1].text)
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(
                payload.get('content')).get("fields"))
        assert MockTab.get_from_tabs(payload.get('content')).get('show_if') == MockTab.SHOW_IF

    def test_update_summary_layout(self, fx_soar_adapter):
        update_summary_layout(
            OPTS,
            ui_components_to_add=[
                Section(
                    element_list=[Header("Summary"), HTMLBlock("<b>Parent Incident</b>"), Field("id")],
                    show_if=[Field("city").conditions.equals("test")]
                )
            ],
            header_of_block_to_add_after="Summary"
        )

        assert fx_soar_adapter.call_count == 3
