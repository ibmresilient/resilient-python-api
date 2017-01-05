# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

""" Requests mock for Resilient REST API """

import logging
import json
import requests
import requests_mock
from resilient_test_tools.resilient_rest_mock import ResilientMock, resilient_endpoint
LOG = logging.getLogger(__name__)


class MyResilientMock(ResilientMock):

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
        with open("saved_responses/200_JSON_GET__rest_orgs_201_incidents_2233__2017-01-04T09:33:35.794895") as json_data:
            incident_data =   json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=incident_data)

    @resilient_endpoint("PUT", "/incidents/[0-9]+")
    def incident_put(self, request):
        """ Callback for PUT to /orgs/<org_id>/incidents/<inc_id> """
        LOG.debug("incident_put")
        with open("saved_responses/200_JSON_PUT__rest_orgs_201_incidents_2233__2017-01-04T09:33:37.065467") as json_data:
            incident_data =   json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=incident_data)

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
        with open("saved_responses/200_JSON__rest_orgs_201_types_incident_fields__2016-12-06T21:02:12.665008") as json_data:
            field_data =  json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=field_data)

    @resilient_endpoint("GET", "/types/actioninvocation/fields")
    def action_fields_get(self, request):
        """ Callback for GET to /orgs/<org_id>/types/actioninvocation/fields """
        LOG.debug("action_fields_get")
        with open("saved_responses/200_JSON_GET__rest_orgs_201_types_actioninvocation_fields__2017-01-04T09:33:25.179943") as json_data:
            field_data = json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=field_data)

    @resilient_endpoint("GET", "/actions")
    def actions_get(self, request):
        """ Callback for GET to /orgs/<org_id>/actions """
        LOG.debug("actions_get")
        with open("saved_responses/200_JSON_GET__rest_orgs_201_actions__2017-01-04T09:33:25.024279") as json_data:
            action_data = json.load(json_data)
            return requests_mock.create_response(request,
                                                 status_code=200,
                                                 json=action_data)
