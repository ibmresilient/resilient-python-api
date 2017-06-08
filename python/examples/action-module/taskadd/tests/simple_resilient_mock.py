""" Requests mock for Resilient REST API for Task Add Component """

import json
import os.path
import requests
import requests_mock
from co3.resilient_rest_mock import ResilientMock, resilient_endpoint

class SimpleResilientMock(ResilientMock):

    def _create_response_from_file(self, file_path, request):
        """ Generate response from file contents """
        with open(file_path) as json_data:
            incident_data = json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=incident_data)

    @resilient_endpoint("POST", "/rest/session")
    def session_post(self, request):
        """ Callback for POST to /rest/session """
        with open(os.path.join("logged_responses",
                               "200_JSON_POST__rest_session__2017-03-07T15-06-32.499832")) as json_data:
            session_data = json.load(json_data)
            session_data["orgs"][1]["name"] = self.org_name
            session_data["user_email"] = self.email
            cookies = {'JSESSIONID': 'FakeSessionId'}
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 cookies=requests.cookies.cookiejar_from_dict(cookies),
                                                 json=session_data)
    
    @resilient_endpoint("POST", "/incidents/[0-9]+/tasks$")
    def task_post(self, request):
        """ Callback for POST to /orgs/<org_id>/incidents/<inc_id>/tasks """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_POST__rest_orgs_211_incidents_4573_tasks__2017-03-07T15-07-14.890616"),
                                               request)

    @resilient_endpoint("GET", "/orgs/[0-9]+$")
    def org_get(self, request):
        """ Callback for GET to /orgs/<org_id> """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211__2017-03-07T15-06-32.631724"),
                                               request)

    @resilient_endpoint("GET", "/types/incident/fields$")
    def incident_fields_get(self, request):
        """ Callback for GET to /orgs/<org_id>/types/incident/fields """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211_types_incident_fields__2017-03-07T15-06-32.838415"),
                                               request)

    @resilient_endpoint("GET", "/types/actioninvocation/fields$")
    def action_fields_get(self, request):
        """ Callback for GET to /orgs/<org_id>/types/actioninvocation/fields """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211_types_actioninvocation_fields__2017-03-07T15-06-33.664072"),
                                               request)

    @resilient_endpoint("GET", "/actions$")
    def actions_get(self, request):
        """ Callback for GET to /orgs/<org_id>/actions """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211_actions__2017-03-07T15-06-33.143165"),
                                               request)

    @resilient_endpoint("GET", "/users/[0-9]+$")
    def user_get(self, request):
        """ Callback for GET to /orgs/<org_id>/users/<user_id> """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211_users_115__2017-03-07T15-07-14.289859"),
                                               request)

    @resilient_endpoint("PUT", "/incidents/[0-9]+/members$")
    def members_put(self, request):
        """ Callback for PUT to /orgs/<org_id>/incidents/<inc_id>/members """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_PUT__rest_orgs_211_incidents_4573_members__2017-03-07T15-07-14.611240"),
                                               request)

    @resilient_endpoint("GET", "/incidents/[0-9]+/members$")
    def members_get(self, request):
        """ Callback for GET to /orgs/<org_id>/incidents/<inc_id>/members """
        return self._create_response_from_file(os.path.join("logged_responses",
                                                            "200_JSON_GET__rest_orgs_211_incidents_4573_members__2017-03-07T15-07-14.353816"),
                                               request)
