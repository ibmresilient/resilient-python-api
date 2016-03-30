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
Action to add a group based on the change of a boolean field
"""

from __future__ import print_function
import logging

import requests

from circuits import Component
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


class GroupAddAction(ResilientComponent):
    '''

    # invoked when a field CSIRT changes to True, adding an incident Type of CSIRT
    # to the incident

    #the function map maps the action name to a specific handling method within
    # this object.  The mapping table is used to determine if the action has
    # an associated function in the handler
    # the function/method name MUST be the same as the action as defined in resilient
    # Note action names are not the same as the Display Name in the action definition
    #
    # The display name for this action is "CSIRTAction", it's system level name is
    # csirtaction
    '''

    def __init__(self, opts):
        super(GroupAddAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        self.actiondata = opts.get(CONFIG_ACTION_SECTION, {})

        #self.sync_file = os.path.dirname(os.path.abspath(self.sync_opts.get('mapfile')))

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "dt_action")

        # set up the resilient connection for the source which
        # is where the action will get fired from
        # destination will open a unique resorg object each Time
        # a connection needs to be made.
        self.reso = ResOrg(client=self.rest_client)

        self.group_to_add = self.actiondata.get("group")
        self.incidenttype = self.actiondata.get("incidenttype")
        self.userlist = self.reso.get_users()
        self.grouplist = self.reso.get_groups()

    @handler("group_add")
    def _group_action(self, event, *args, **kwargs):
        """The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameters
           (event, *args, **kwargs), and ignore any messages that are not
           from the Actions module.
        """
        if not isinstance(event, ActionMessage):
            # Some event we are not interested in
            return

        log.debug("Event Name {}".format(event.name))

        func = self.get_action_function(event.name) # determine which method to invoke based on the event name

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

    def group_add(self, args):
        """
        Method invoked by action MUST be the action name as defined in the system
        """
        def apply_change(incident):
            """
            function invoked by get_put to update the incident fields
            """
            log.debug("Applying change for get put")
            incident['members'].append(gid)


        log.debug("group_add action function")

        # get the full incident
        incident = self.reso.get_incident_by_id(args.incident.get('id'))
        
        incident_types = self.reso.get_incident_types()
       
        # get the current incident type id's and map them to the name
        named_itypes = []
        for itype in incident.get('incident_type_ids'):
            name = self.reso.map_incident_type_id_to_name(incident_types, itype)
            if name is not None:
                log.debug("incident type id {} == {}".format(itype, name))
                named_itypes.append(name)

        if named_itypes and self.incidenttype in named_itypes:
            # need to chedk for the group being in the member list or
            # being the owner id.. no reason to update the membership
            # incident['members'] and incident['owner_id']
            gid = self.reso.get_user_id(self.grouplist, self.group_to_add)
            if gid is None:
                log.error("Group specified in the configuration does not exist {}".format(self.group_to_add))
                raise Exception("Group specified in the configuration does not exist {}".format(self.group_to_add))

            if  incident.get('owner_id') == gid or gid in incident.get('members'):
                log.info("{} is already a member or the owner of the case".format(self.group_to_add))
                return "Action complete already member"

            try:
                self.reso.client().get_put('/incidents/{}'.format(incident.get('id')), apply_change)
            except Exception as ecode:
                log.error("Failed to update incident {} with error: {}".format(incident.get('id'), ecode))
                raise Exception("Failed to update incident {} with error: {}".format(incident.get('id'), ecode))


        else:
            log.info("Incident type {} is not in the incident type list".format(self.incidenttype))

        return "action complete action completed"


    def get_action_function(self, funcname):
        '''
        map the name passed in to a method within the object
        '''

        log.debug("get function {}".format(funcname))
        return getattr(self, '%s'%funcname, None)






