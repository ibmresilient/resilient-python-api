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

"""Class that does the main work, duplicating an incident"""

from __future__ import print_function
from __future__ import absolute_import

import json
import logging
import copy
import os
import tempfile
import time

logger = logging.getLogger(__name__)

ACTION_OBJECT_TYPES = {0: "Incident",
                       1: "Task",
                       2: "Note",
                       3: "Milestone",
                       4: "Artifact",
                       5: "Attachment"}


class CrossOrgActions(object):
    """
    Receive messages from Resilient actions, and handle them.
    """

    def __init__(self, opts, resilient_client, dest_resilient_client):
        self.opts = opts
        self.src_client = resilient_client
        self.dest_client = dest_resilient_client


    def handle_message(self, message, context_token):
        """Handle a message from the Resilient queue"""
        logger.debug("Received message\n%s", json.dumps(message, indent=2))

        # Validate the type of message
        object_type = message["object_type"]
        action_type = ACTION_OBJECT_TYPES[object_type]
        action_id = message["action_id"]

        # For convenience, fetch a new copy of the incident with all its field values as names
        incident = message["incident"]
        incident_id = incident['id']
        incident = self.src_client.get("/incidents/{}?handle_format=names".format(incident_id))

        logger.info('Received action %s for incident %s: type=%s; name=%s',
                    action_id, incident_id, action_type, incident['name'])

        self.new_incident_from_artifact(incident, message)


    def new_incident_from_artifact(self, incident, message=None):
        """Generate a new incident"""
        # The artifact_value is (e.g.) a system name or host name,
        # this function creates a new incident copying the existing incident
        # and some of its content:
        # - attachments (if 'copy_attachments' is true)
        # - notes (if 'copy_notes' is true)
        # After the new incident is created, we update the original incident
        # to indicate that this action was taken.
        artifact = message["artifact"]
        if not artifact:
            logger.error("This action must be initiated from an artifact.")
            return

        action_fields = message["type_info"]["actioninvocation"]["fields"]
        incident_fields = message["type_info"]["incident"]["fields"]
        artifact_fields = message["type_info"]["artifact"]["fields"]

        artifact_value = artifact["value"]
        artifact_type = artifact["type"]
        artifact_type_name = artifact_fields["type"]["values"][str(artifact_type)]["value"]

        now_ts = int(time.time() * 1000)

        # Options from the action fields
        option_copy_attachments = message["properties"].get("copy_attachments", True)
        option_copy_notes = message["properties"].get("copy_notes", True)
        new_incident_type = message["properties"].get("new_incident_type")
        new_incident_description = message["properties"].get("new_incident_description", "")

        # Resolve the new incident type id to its name, or default to "Malware"
        new_incident_type_name = None
        if new_incident_type:
            new_incident_type_name = action_fields["new_incident_type"]["values"][str(new_incident_type)]["value"]
        new_incident_type = new_incident_type_name or "Malware"

        logger.info("new_incident_from_artifact: %s, type %s", new_incident_description, new_incident_type)
        logger.debug(incident.keys())

        # Make a new incident by copying all fields from the original
        tmp_incident = copy.deepcopy(incident)
        tmp_incident.pop("id", None)
        tmp_incident.pop("cm", None)
        tmp_incident.pop("creator", None)
        tmp_incident.pop("phase_id", None)
        tmp_incident.pop("plan_status", None)
        tmp_incident.pop("task_changes", None)
        tmp_incident.pop("create_date", None)

        tmp_incident["name"] = "{} (from: {})".format(artifact_value, incident["name"])
        tmp_incident["description"] = new_incident_description
        tmp_incident["incident_type_ids"] = [new_incident_type]

        # For demonstration ONLY: remove all custom fields
        # (because they may not be present on the target org).
        # You may want to copy some or all custom fields to the destination,
        # depending on the customizations in your environment.
        tmp_incident["properties"] = None

        # Create the new incident
        new_incident = self.dest_client.post("/incidents", tmp_incident)
        logger.info("Created new incident: %s", new_incident["id"])

        # Copy the one artifact
        tmp_artifact = {"description": artifact["description"],
                        "type": artifact_type_name,
                        "value": artifact_value}
        new_artifact = self.dest_client.post("/incidents/{}/artifacts".format(new_incident["id"]), tmp_artifact)
        logger.info("Created new artifact: %s on incident: %s", new_artifact, new_incident["id"])

        # Add a milestone to the original incident
        mdesc = "Artifact '{}' was escalated to a new incident ({}) in '{}'".format(artifact_value, new_incident["id"], self.opts["destorg"])
        tmp_milestone = {"date": now_ts,
                         "description": mdesc,
                         "title": "Artifact '{}' escalated".format(artifact_value)}
        new_milestone = self.src_client.post("/incidents/{}/milestones".format(incident["id"]), tmp_milestone)
        logger.info("Created new milestone: %s on incident: %s", new_milestone["id"], incident["id"])

        # Add a milestone to the new incident
        mdesc = "Created from incident {} in '{}'".format(incident["id"], self.opts["org"])
        tmp_milestone = {"date": now_ts,
                         "description": mdesc,
                         "title": "Escalated from '{}'".format(self.opts["org"])}
        new_milestone = self.dest_client.post("/incidents/{}/milestones".format(new_incident["id"]), tmp_milestone)
        logger.info("Created new milestone: %s on incident: %s", new_milestone["id"], new_incident["id"])

        # Copy other parts of the incident
        if option_copy_attachments:
            self.copy_attachments(incident, new_incident)

        if option_copy_notes:
            self.copy_notes(incident, new_incident)

        # Leave the original incident's fields unchanged
        return incident


    def copy_attachment(self, attachment, from_incident, to_incident):
        attname = attachment["name"]
        inc_id = from_incident["id"]
        to_inc_id = to_incident["id"]
        att_id = attachment["id"]
        tempfilename = os.path.join(tempfile.gettempdir(), os.path.basename(attname).replace(" ", "_"))
        logger.debug("inc_id %s att_id %s to_inc_id %s %s", inc_id, att_id, to_inc_id, tempfilename)
        try:
            with open(tempfilename, "w+b") as temp:
                tempfilename = temp.name
                data = self.src_client.get_content("/incidents/{}/attachments/{}/contents".format(inc_id, att_id))
                temp.write(data)
            new_att = self.dest_client.post_attachment("/incidents/{}/attachments".format(to_inc_id), tempfilename)
            logger.debug("att: %s", new_att)
        finally:
            os.remove(tempfilename)

    def copy_attachments(self, from_incident, to_incident):
        attachments = self.src_client.get("/incidents/{}/attachments".format(from_incident["id"]))
        for attachment in attachments:
            try:
                self.copy_attachment(attachment, from_incident, to_incident)
            except:
                logger.exception("Failed to copy attachment %s", attachment["name"])
                # Carry on regardless

    def copy_note(self, note, parent_note, from_incident, to_incident):
        tmp_note = {}
        tmp_note["text"] = note.get("text", "")
        if parent_note:
            tmp_note["parent_id"] = parent_note["id"]
        logger.debug("note: %s", tmp_note)
        new_note = self.dest_client.post("/incidents/{}/comments".format(to_incident["id"]), tmp_note)
        for child in note.get("children", []):
            self.copy_note(child, new_note, from_incident, to_incident)

    def copy_notes(self, from_incident, to_incident):
        notes = self.src_client.get("/incidents/{}/comments".format(from_incident["id"]))
        for note in notes:
            self.copy_note(note, None, from_incident, to_incident)
