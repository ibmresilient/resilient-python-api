#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import json

from mock import patch
from resilient_circuits.util.resilient_customize import Customizations
from resilient import helpers as res_helpers


def test_customizations_load_import(fx_simple_client, fx_read_mock_definition):
    """
    This is a real basic test just confirming that our move of res_helpers.remove_tag works.
    We test resilient.remove_tag separately
    """

    simple_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    import_def = fx_read_mock_definition

    simple_client.get_put = lambda x, y: True

    mock_uri = "{0}/rest/orgs/{1}/configurations/imports".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps({"id": 123, "status": "PENDING"}))

    mock_uri = "{0}/rest/orgs/{1}/configurations/imports/123".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('PUT', mock_uri, status_code=200, text=json.dumps({"id": 123, "status": "DONE"}))

    mock_uri = "{0}/rest/orgs/{1}/message_destinations".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps({"entities": [{"id": 1, "programmatic_name": "fn_main_mock_integration"}]}))

    c = Customizations(simple_client, False)

    with patch("resilient_circuits.util.resilient_customize.Customizations.confirm") as mock_prompt:
        mock_prompt.return_value = True

        with patch("resilient.helpers.remove_tag", new=res_helpers.remove_tag) as mock_remove_tag:

            c.load_import(import_def, "mock instance")
