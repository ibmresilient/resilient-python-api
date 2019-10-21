#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import requests
import requests_mock
from resilient.resilient_rest_mock import ResilientMock, resilient_endpoint
from tests.shared_mock_data import resilient_api_mock_data as mock_data


class ResilientAPIMock(ResilientMock):

    @resilient_endpoint("POST", "/rest/session")
    def post_session(self, request):
        """
        Mock POST /rest/session
        """
        return requests_mock.create_response(request,
                                             status_code=200,
                                             cookies=requests.cookies.cookiejar_from_dict({'JSESSIONID': 'FakeSessionId'}),
                                             json=mock_data.SESSION_DATA)

    @resilient_endpoint("GET", "/orgs/[0-9]+$")
    def get_org(self, request):
        """
        Mock GET /orgs/<org_id>
        """
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=mock_data.ORG_DATA)
