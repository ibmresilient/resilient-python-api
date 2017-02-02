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
            # Action was initiated from an artifact.
            # Search for the artifact value and produce a set of results
            park_code = message["artifact"]["value"]

        if action_type == "Incident":
            # Action was initiated from an incident.
            # The park code is in the custom field "park" (custom fields within the 'properties' dict)
            park_code_id = message["incident"]["properties"].get("park")
            # In an action message, SELECT fields are delivered as their integer (id) value.
            # To find the text of this field, look up the value in the "type_info" which has the field definition.
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
            park_bears = park_bears or "None"
            return {"park": park_code, "park_name": park_name, "park_bears": park_bears}

        def update_with_park_info(incident, park_info):
            """Update an incident with park info"""
            info = formatted_info(park_info)
            incident["properties"]["park"] = info["park"]
            incident["properties"]["park_name"] = info["park_name"]
            incident["properties"]["park_bears"] = info["park_bears"]

        pinfo = formatted_info(park_info)
        update = (incident["properties"]["park_name"] != pinfo["park_name"]) \
            or (incident["properties"]["park_bears"] != pinfo["park_bears"]) \
            or (incident["properties"]["park"] != pinfo["park"])
        if update:
            logger.info("Updated")
            self.client.get_put("/incidents/{}".format(incident["id"]),
                                lambda incident: update_with_park_info(incident, park_info))
        else:
            logger.info("No change")


def test():
    """main"""
    worker = ParkActions(None, None)
    park = worker.park_search("SAMA")
    print(json.dumps(park, indent=4))


if __name__ == "__main__":
    test()
