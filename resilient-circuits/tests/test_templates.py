#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

from resilient_circuits.template_functions import environment, render, render_json

def test_environment():
    env = environment()
    for custom in ['soar_datetimeformat', 'soar_substitute', 'soar_trimlist', 'soar_splitpart',
                   'pretty', 'js', 'json', 'html', 'idna', 'ps', 'iso8601',
                   'punycode', 'ldap']:
        assert custom in env.filters

def test_render():
    assert render("{{ url_data | url }}", { "url_data": "https://ibm.com?something=here"}) == "https%3A//ibm.com%3Fsomething%3Dhere"
    assert render("{{ lookup | soar_substitute('{ \"info\": \"low\"}') }}", { "lookup": "info"}) == "low"

def test_render_json():
    assert render_json('{ "date": "{{ iso8601_date | iso8601 }}" }', { "iso8601_date": 1645820357000 }) == { "date": "2022-02-25T20:19:17+00:00" }
    assert render_json('{ "date": {{ datetime | soar_datetimeformat(split_at="+") }} }', { "datetime": "2022-02-25T20:19:17+00:00" }) == { "date": 1645820357000 }