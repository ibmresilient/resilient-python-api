#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import requests
import requests_mock
from resilient.resilient_rest_mock import ResilientMock, resilient_endpoint
from tests.helpers import read_mock_json


class ResilientAPIMock(ResilientMock):

    @resilient_endpoint("POST", "/rest/session")
    def post_session(self, request):
        """
        Mock POST /rest/session
        """
        return requests_mock.create_response(request,
                                             status_code=200,
                                             cookies=requests.cookies.cookiejar_from_dict({'JSESSIONID': 'FakeSessionId'}),
                                             json=read_mock_json("session.JSON"))

    @resilient_endpoint("GET", "/orgs/[0-9]+$")
    def get_org(self, request):
        """
        Mock GET /orgs/<org_id>
        """
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=read_mock_json("orgs.JSON"))

    @resilient_endpoint("POST", "/configurations/exports/")
    def post_export(self, request):
        """
        Mock POST /configurations/exports/
        """
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=read_mock_json("export.JSON"))
