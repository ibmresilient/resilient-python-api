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
Action to add a task through a manual action with
3 fields defined for the manual action
"""

import logging
import requests

from circuits import Component, Debugger
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage

requests.packages.urllib3.disable_warnings()

# Lower the logging threshold for requests
logging.getLogger("requests.packages.urllib3").setLevel(logging.ERROR)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.Formatter('%(asctime)s:%(name)s:%(levelname)-8s %(message)s')

CONFIG_DATA_SECTION = 'task_add'
CONFIG_SOURCE_SECTION = 'resilient'


class AddTaskAction(ResilientComponent):
    """
    Manual action to add an incident task to a phase
    """

    def __init__(self, opts):
        super(AddTaskAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "dt_action")

    @handler()
    def add_task_action(self, event, *args, **kwargs):
        """The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameters
           (event, *args, **kwargs), and ignore any messages that are not
           from the Actions module.
        """
        if not isinstance(event, ActionMessage):
            # Some event we are not interested in
            log.debug("Ignoring Event: ", str(event))
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

        #end add_task_action


    def add_task(self, args):
        """
        Method invoked based on action name
        """
        log.debug("Invoked function")

        incident_id=args.message['incident']['id']
        tname = args.properties.get('task_name')
        task_instructions = args.properties.get('task_instructions')
        task_phase_key = args.properties.get('task_phase')
        task_phase = args.message.get('type_info', {}).get(
            'actioninvocation', {}).get('fields', {}).get(
                'task_phase', {}).get('values', {}).get(
                    str(task_phase_key), {}).get('label', None)

        task = {"name": tname or '',
                "instr_text": task_instructions or '',
                "inc_id": incident_id,
                "phase_id": task_phase or ''}

        posted_task = self.rest_client().post("/incidents/%s/tasks" % incident_id, task)
        if not posted_task:
            log.error("Failed to post task!")
            return "Error posting task"
        else:
            log.info("Task Posted: %s", posted_task)
            return "action complete. task posted"
    

    def get_action_function(self, funcname):
        """
        map the name passed in to a method within the object
        """

        log.debug("get function {}".format(funcname))
        return getattr(self, '%s'%funcname, None)








