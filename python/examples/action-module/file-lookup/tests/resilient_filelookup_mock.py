""" Requests mock for Resilient REST API """

import logging
import json
import os.path
import requests
import requests_mock
from co3.resilient_rest_mock import ResilientMock, resilient_endpoint
LOG = logging.getLogger(__name__)


class MyResilientMock(ResilientMock):

    def __init__(self, *args, **kwargs):
        super(MyResilientMock,self).__init__(*args, **kwargs)
        with open(os.path.join("tests",
                               "responses",
                               "200_JSON_GET__rest_orgs_201_incidents_2314__2017-01-30T11-09-38.662431")) as json_data:
            self.incident =   json.load(json_data)

    @resilient_endpoint("POST", "/rest/session")
    def session_post(self, request):
        """ Callback for POST to /rest/session """
        LOG.debug("session_post")
        session_data = {
            "saml_alias": None,
            "csrf_token": "79945884c2e6f2339cbffbbaba01f17b",
            "user_lname": "Doe",
            "user_id": 1,
            "is_ldap": False,
            "is_saml": False,
            "orgs": [
                {
                    "city": "AnyCity",
                    "addr": None,
                    "zip": None,
                    "has_available_twofactor": False,
                    "perms": {
                        "create_shared_layout": True,
                        "administrator": False,
                        "create_incs": True,
                        "master_administrator": True,
                        "observer": False
                    },
                    "supports_ldap": False,
                    "enabled": True,
                    "twofactor_auth_domain": None,
                    "attachments_enabled": True,
                    "has_saml": False,
                    "state": None,
                    "addr2": None,
                    "twofactor_cookie_lifetime_secs": 0,
                    "require_saml": False,
                    "tasks_private": False,
                    "authorized_ldap_group": None,
                    "id": 201,
                    "name": self.org_name
                },
                {
                    "city": None,
                    "addr": None,
                    "zip": None,
                    "has_available_twofactor": False,
                    "perms": {
                        "create_shared_layout": True,
                        "administrator": False,
                        "create_incs": True,
                        "master_administrator": True,
                        "observer": False
                    },
                    "supports_ldap": False,
                    "enabled": True,
                    "twofactor_auth_domain": None,
                    "attachments_enabled": True,
                    "has_saml": False,
                    "state": None,
                    "addr2": None,
                    "twofactor_cookie_lifetime_secs": 0,
                    "require_saml": False,
                    "tasks_private": False,
                    "authorized_ldap_group": None,
                    "id": 202,
                    "name": "Mock Org"
                }
            ],
            "session_ip": "192.168.56.1",
            "user_fname": "John",
            "user_email": self.email
        }
        cookies = {'JSESSIONID': 'FakeSessionId'}
        return requests_mock.create_response(request,
                                             status_code=200,
                                             cookies=requests.cookies.cookiejar_from_dict(cookies),
                                             json=session_data)

    @resilient_endpoint("GET", "/incidents/[0-9]+$")
    def incident_get(self, request):
        """ Callback for GET to /orgs/<org_id>/incidents/<inc_id> """
        LOG.debug("incident_get")
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=self.incident)

    @resilient_endpoint("PUT", "/incidents/[0-9]+")
    def incident_put(self, request):
        """ Callback for PUT to /orgs/<org_id>/incidents/<inc_id> """
        LOG.debug("incident_put")
        self.incident = request.json()
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=self.incident)

    @resilient_endpoint("POST", "/incidents/")
    def incident_post(self, request):
        """ Callback for POST to /orgs/<org_id>/incidents """
        LOG.debug("incident_post")
        self.incident = request.json()
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=self.incident)

    @resilient_endpoint("GET", "/orgs/[0-9]+$")
    def org_get(self, request):
        """ Callback for GET to /orgs/<org_id> """
        LOG.debug("org_get")
        org_data = { "users": {"2": { "id": 2,
                                      "fname": "Resilient",
                                      "lname": "Sysadmin",
                                      "status": "A",
                                      "email": self.email,
                                      "phone": None,
                                      "cell": None,
                                      "title": None,
                                      "notes": None,
                                      "locked": False,
                                      "enabled": True,
                                      "roles": {
                                          "administrator": False,
                                          "observer": False,
                                          "master_administrator": True,
                                          "create_incs": True
                                      },
                                      "last_login": 1475614308048,
                                      "org_id": 202,
                                      "group_ids": [],
                                      "is_external": False},
                               "3": {
                                   "id": 3,
                                   "fname": "Jim",
                                   "lname": "Beam",
                                   "status": "A",
                                   "email": "someone@somewhere.com",
                                   "phone": None,
                                   "cell": None,
                                   "title": None,
                                   "notes": None,
                                   "locked": False,
                                   "enabled": True,
                                   "roles": {
                                       "administrator": False,
                                       "observer": False,
                                       "master_administrator": True,
                                       "create_incs": True},
                                   "last_login": 1476711664869,
                                   "org_id": 202,
                                   "group_ids": [],
                                   "is_external": False}},
                     "actions_framework_enabled": True,
        }
        return requests_mock.create_response(request,
                                             status_code=200,
                                             json=org_data)

    @resilient_endpoint("GET", "/types/incident/fields")
    def incident_fields_get(self, request):
        """ Callback for GET to /orgs/<org_id>/types/incident/fields """
        LOG.debug("incident_fields_get")
        with open(os.path.join("tests",
                               "responses",
                               "200_JSON_GET__rest_orgs_201_types_incident_fields__2017-01-30T11-09-07.129108")) as json_data:
            field_data =  json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=field_data)

    @resilient_endpoint("GET", "/types/actioninvocation/fields")
    def action_fields_get(self, request):
        """ Callback for GET to /orgs/<org_id>/types/actioninvocation/fields """
        LOG.debug("action_fields_get")
        with open(os.path.join("tests",
                               "responses",
                               "200_JSON_GET__rest_orgs_201_types_incident_fields__2017-01-30T11-09-07.129108")) as json_data:
            field_data = json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=field_data)

    @resilient_endpoint("GET", "/actions")
    def actions_get(self, request):
        """ Callback for GET to /orgs/<org_id>/actions """
        LOG.debug("actions_get")
        with open(os.path.join("tests",
                               "responses",
                               "200_JSON_GET__rest_orgs_201_actions__2017-01-30T11-09-07.183063")) as json_data:
            action_data = json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=action_data)
