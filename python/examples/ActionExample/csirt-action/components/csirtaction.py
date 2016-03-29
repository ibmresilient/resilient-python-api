#!/usr/bin/env python

# -*- coding: utf-8 -*-
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
"""
Action to add incident type of CSIRT when a boolean field changes
"""

from __future__ import print_function
import logging

import requests

from circuits import Component, Debugger
from circuits.core.handlers import handler

from resilient_circuits.actions_component import ResilientComponent, ActionMessage
from ResilientOrg import ResilientOrg as ResOrg

requests.packages.urllib3.disable_warnings()

# Lower the logging threshold for requests
logging.getLogger("requests.packages.urllib3").setLevel(logging.ERROR)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.Formatter('%(asctime)s:%(name)s:%(levelname)-8s %(message)s')


#log.setLevel(logging.DEBUG)  # force logging level to be DEBUG
CONFIG_DATA_SECTION = 'action'
CONFIG_SOURCE_SECTION = 'resilient'
CONFIG_ACTION_SECTION = 'actiondata'


class CSIRTAction(ResilientComponent):
    """
    invoked when a field CSIRT changes to True, adding an incident Type of CSIRT
    to the incident

    the function map maps the action name to a specific handling method within
    this object.  The mapping table is used to determine if the action has
    an associated function in the handler
    the function/method name MUST be the same as the action as defined in resilient
    Note action names are not the same as the Display Name in the action definition

    The display name for this action is "CSIRTAction", it's system level name is
    csirtaction
    """

    def __init__(self, opts):
        super(CSIRTAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        self.actiondata = opts.get(CONFIG_ACTION_SECTION, {})

        #self.sync_file = os.path.dirname(os.path.abspath(self.sync_opts.get('mapfile')))

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "dt_action")

        '''
        set up the resilient connection for the source which
        is where the action will get fired from
        destination will open a unique resorg object each Time
        a connection needs to be made.
        '''
        self.reso = ResOrg(client=self.rest_client)

        self.new_incident_type = self.actiondata.get("incidenttype")


    @handler("csirtaction")
    def _csirt_action(self, event, *args, **kwargs):
        """
           The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameter
           (event, *args, **kwargs), and ignore any messages that are not
           from the Actions module.
        """
        if not isinstance(event, ActionMessage):
            # Some event we are not interested in
            return

        log.debug("Event Name {}".format(event.name))

        # determine which method to invoke based on the event name
        func = self.get_action_function(event.name)
        if func is not None:
            retv = func(event)
            if retv:
                yield retv
            else:
                yield "event handled"
        else:
            # an action without a handling method was put onto the queue
            raise Exception("Invalid event - no function to handle")

        #end _invite_action


    def csirtaction(self, args):
        """
        Method to invoke based on action name in system
        """
        log.debug("csirt action function")

        # get the full incident
        incident = self.reso.get_incident_by_id(args.incident.get('id'))
        incident_types = self.reso.get_incident_types()

        log.debug("looking for incident type {}".format(self.new_incident_type))
        new_itype_id = self.reso.get_incident_type_id(incident_types, self.new_incident_type)
        log.debug("new incident type id: {}".format(new_itype_id))

        # if the new incident type does not exist, raise exception so the action will faile
        if new_itype_id is  None:
            log.error("New incident type specified is not in the Resilient org configuration")
            raise Exception("Can not find incident type {} that is configured".format(self.new_incident_type))


        def apply_change(incident):
            log.debug("Applying change for get put")
            incident['incident_type_ids'].append(new_itype_id)

        if new_itype_id in incident.get('incident_type_ids'):
            log.info("Action completed new type already exists")
            return "Action completed >{}< type already exists in case".format(self.new_incident_type)

        try:
            log.debug("Attempting to get_put the incident")
            newincident = self.reso.client().get_put('/incidents/{}'.format(incident.get('id')),
                                                     apply_change)
        except Exception as ecode:
            log.error("Failed to update the incident {} with the new incident type:{}".format(incident.get('id'),
                      self.new_incident_type))
            log.error("Get/Put failed with {}".format(ecode))
            raise Exception("Failed to update incident")

        return "action complete action completed"


    def get_action_function(self, funcname):
        """
        map the name passed in to a method within the object
        """

        log.debug("get function {}".format(funcname))
        return getattr(self, '%s'%funcname, None)






