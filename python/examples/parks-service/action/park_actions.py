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

"""Class that does the main work, searching the Parks Service and posting results"""

from __future__ import print_function
from __future__ import absolute_import

import json
import logging
import suds.client

logger = logging.getLogger(__name__)

MAXRESULTS = 100

ACTION_OBJECT_TYPES = {0: "Incident",
                       1: "Task",
                       2: "Note",
                       3: "Milestone",
                       4: "Artifact",
                       5: "Attachment"}


class ParkActions(object):
    """
    Receive messages from Resilient actions on an Artifact.
    Send the artifact to the Parks Service.
    Place any results in the incident.
    """

    def __init__(self, opts, resilient_client, park_url="http://localhost:9000/cmdb.asmx"):
        self.opts = opts
        self.client = resilient_client

        # Initialize a SOAP client for the Parks Service
        park_wsdl = park_url + "?wsdl"
        logger.info(park_wsdl)
        self.parks_service = suds.client.Client(park_wsdl,
                                                location=park_url,
                                                headers=dict(),
                                                cache=suds.cache.NoCache(),
                                                prefixes=True)


    def park_search(self, park_code):
        """Search for park code, return all park info"""
        park_info = self.parks_service.service.GetParkDetails(park_code)
        logger.info(park_info)

        # Copy from the suds type into a dict() for easier handling
        park_dict = dict()
        for (name, value) in park_info:
            park_dict[name] = value

        return park_dict


    def handle_message(self, message, context_token):
        """Handle a message from the Resilient queue"""
        logger.debug("Received message\n%s", json.dumps(message, indent=2))

        # Validate the type of message
        object_type = message["object_type"]
        action_type = ACTION_OBJECT_TYPES[object_type]
        action_id = message["action_id"]

        # Validate that we have incident object fields necessary
        incident = message["incident"]
        incident_id = incident['id']

        logger.info('Received action %s for incident %s: type=%s; name=%s',
                     action_id, incident_id, action_type, incident['name'])

        park_code = None
        if action_type == "Artifact":
            # Search for artifact and produce a set of results
            park_code = message["artifact"]["value"]

        if action_type == "Incident":
            park_code_id = message["incident"]["properties"].get("park")
            park_code = message["type_info"]["incident"]["fields"]["park"]["values"][str(park_code_id)]["label"]

        logger.info("Park code: %s", park_code)
        park_info = self.park_search(park_code)

        # logger.info('Uploading results as %s', result_file)
        # self.client.post_attachment('/incidents/{}/attachments'.format(incident_id), result_file)
        # os.remove(result_file)

        # If the results are different - update the incident
        def formatted_info(park_info):
            """Produce the string representations of the park and its bears"""
            park_code = park_info.get("parkCode")
            park_name = park_info.get("parkName")
            park_bears_list = []
            if park_info.get("hasBlackBear"):
                park_bears_list.append("Black")
            if park_info.get("hasGrizzlyBear"):
                park_bears_list.append("Grizzly")
            if park_info.get("hasPolarBear"):
                park_bears_list.append("Polar")
            park_bears = ",".join(park_bears_list)
            if park_bears == "": park_bears = "None"
            return {"park": park_code, "park_name": park_name, "park_bears": park_bears}

        def update_with_park_info(incident, park_info):
            """Update an incident with park info"""
            info = formatted_info(park_info)
            incident["properties"]["park"] = info["park"]
            incident["properties"]["park_name"] = info["park_name"]
            incident["properties"]["park_bears"] = info["park_bears"]

        update_func = lambda incident: update_with_park_info(incident, park_info)

        pinfo = formatted_info(park_info)
        update = (incident["properties"]["park_name"] != pinfo["park_name"]) or (incident["properties"]["park_bears"] != pinfo["park_bears"]) or (incident["properties"]["park"] != pinfo["park"])
        if update:
            logger.info("Updated")
            self.client.get_put("/incidents/{}".format(incident["id"]), update_func)
        else:
            logger.info("No change")


def test():
    """main"""
    worker = ParkActions(None, None)
    park = worker.park_search("SAMA")
    print(json.dumps(park, indent=4))


if __name__ == "__main__":
    test()
