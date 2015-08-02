#!/usr/bin/env python

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

"""Class that does the main work"""

from __future__ import print_function
from __future__ import absolute_import

import json
import logging
import ldap3

from ldap3 import Server, Connection
from ldap3.utils.conv import escape_bytes

logger = logging.getLogger(__name__)

OBJECT_TYPE_ARTIFACT = 4

LDAP_DEFAULT_PORT = 389

LDAP_AUTH_TYPES = {"ANONYMOUS": ldap3.ANONYMOUS,
                   "SIMPLE": ldap3.SIMPLE,
                   "SASL": ldap3.SASL,
                   "NTLM": ldap3.NTLM}



def update_with_result(artifact, result):
    """Function to update the artifact, adding result to its description"""
    desc = artifact["description"] or ""
    if len(desc) > 0:
        desc = desc + "\n\n"
    artifact["description"] = desc + result
    return artifact


class LdapActions(object):
    """
    Receive messages from Resilient actions, and handle them.
    """

    def __init__(self, opts, resilient_client):
        self.opts = opts
        self.client = resilient_client

        # Read the LDAP configuration options
        self.ldap_server = self.opts["ldap"]["server"]
        self.ldap_port = int(self.opts["ldap"]["port"] or LDAP_DEFAULT_PORT)
        self.ldap_user = self.opts["ldap"]["user"]
        self.ldap_password = self.opts["ldap"]["password"]
        self.ldap_ssl = self.opts["ldap"]["ssl"] == "True" # anything else is false
        self.ldap_auth = LDAP_AUTH_TYPES[self.opts["ldap"]["auth"] or "ANONYMOUS"]
        self.ldap_search_base = self.opts["ldap"]["search_base"]
        self.ldap_search_filter = self.opts["ldap"]["search_filter"]


    def handle_message(self, message, context_token):
        """Handle a message from the Resilient queue"""
        logger.debug("Received message\n%s", json.dumps(message, indent=2))

        # Validate the type of message
        action_id = message["action_id"]
        object_type = message["object_type"]
        if object_type != OBJECT_TYPE_ARTIFACT:
            raise Exception("This action must be initiated from an artifact.")

        logger.debug(json.dumps(message, indent=2))

        incident = message["incident"]
        incident_id = incident["id"]

        artifact = message["artifact"]
        artifact_id = artifact["id"]
        artifact_fields = message["type_info"]["artifact"]["fields"]

        artifact_value = artifact["value"]
        artifact_type_id = artifact["type"]
        artifact_type_name = artifact_fields["type"]["values"][str(artifact_type_id)]["label"]

        logger.info("Received action %s for incident %s ('%s'): artifact type=%s, id=%s",
                    action_id, incident_id, incident['name'], artifact_type_name, artifact_id)

        # Search, generating strings
        results = self.ldap_search(artifact_type_name, artifact_value)

        # Join all the strings
        result = "\n".join(results)
        logger.debug(result)
        if len(result) > 0:
            # Update the artifact description
            update_fn = lambda artifact: update_with_result(artifact, result)
            self.client.get_put("/incidents/{}/artifacts/{}".format(incident_id, artifact_id), update_fn, context_token)

    def ldap_search(self, artifact_type_name, artifact_value):
        """Generates strings resulting from the LDAP search"""

        # If there are search_base and search_filter for this specific
        # artifact type, they override the defaults
        search_base = self.opts.get(artifact_type_name, {}).get("search_base", self.ldap_search_base)
        search_filter = self.opts.get(artifact_type_name, {}).get("search_filter", self.ldap_search_filter)

        # Put the artifact value into the seatch filter
        search_filter = search_filter.format(escape_bytes(artifact_value))
        logger.info(search_filter)

        # scope could be BASE, LEVEL or SUBTREE
        search_scope = ldap3.SUBTREE
        # can be a restricted set e.g. ['sn', 'objectClass']
        attribs = [ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES]

        server = Server(self.ldap_server, self.ldap_port, get_info=ldap3.ALL, use_ssl=self.ldap_ssl)
        with Connection(server,
                        auto_bind=True,
                        client_strategy=ldap3.SYNC,
                        user=self.ldap_user,
                        password=self.ldap_password,
                        authentication=self.ldap_auth,
                        check_names=True) as conn:
            logger.debug(server.info)

            # query the LDAP server
            conn.search(search_base, search_filter, search_scope,
                        dereference_aliases=ldap3.DEREF_ALWAYS,
                        attributes=attribs)

            entries = conn.entries
            if entries == None:
                logger.error("No results")
            else:
                yield json.dumps(json.loads(conn.response_to_json())["entries"])


def test_ldap():
    """Test some basic functionality"""
    from ldap import LdapArgumentParser
    opts = LdapArgumentParser().parse_args()
    result = "\n".join(LdapActions(opts, None).ldap_search("String", "nobody"))
    print(result)
    result = "\n".join(LdapActions(opts, None).ldap_search("String", "riemann"))
    print(result)

if __name__ == "__main__":
    test_ldap()
