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

from __future__ import print_function
from circuits import Component, Debugger
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage
import os
import logging


import json
import arrow   # improved Date/Time handling
import tempfile

from pprint import pprint
import json

#from lib.ResOrg import ResOrg

#import ResilientOrg as ResOrg
from ResilientOrg import ResilientOrg as ResOrg
from pprint import pprint
from copy import deepcopy
import time

import requests
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


class AddNoteAction(ResilientComponent):
    '''

     invoked when the phase field is changed

    '''

    def __init__(self, opts):
        super(AddNoteAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        self.actiondata = opts.get(CONFIG_ACTION_SECTION,{})

        #self.sync_file = os.path.dirname(os.path.abspath(self.sync_opts.get('mapfile')))

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "dt_action")

        self.reso = ResOrg(client=self.rest_client)  # set up the resilient connection for the source which 
                                              # is where the action will get fired from
                                              # destination will open a unique resorg object each Time
                                              # a connection needs to be made.


    @handler()
    def _add_note_action(self, event, *args, **kwargs):
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
            rv =func(event)
            if rv:
                yield rv
            else:
                yield "event handled"
        else:
            # an action without a handling method was put onto the queue
            raise Exception("Invalid event - no function to handle")

        #end _invite_action

    def stubfunction(self,args):
        # stub function, can be used to test if the action processor has connected properly
        # create a manual action called "stubfunction" associated with the configured queue
        # and invoke the manual action.  The log will show that the stub function was invoked
        log.debug("Stub Function")
        return "Stub invoked"

    def add_note_on_manual_action(self,args):
        log.debug("Invoked function")


        action_content = args.properties

        note = self.reso.CreateNote(args.message.get('incident').get('id'),args.properties.get('notecontent'))

        return "action complete action completed"


    def get_action_function(self,funcname):
        '''
        map the name passed in to a method within the object
        '''

        log.debug("get function {}".format(funcname))
        return getattr(self,'%s'%funcname,None)








