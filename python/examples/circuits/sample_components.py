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

"""Component examples
   Some example components to handle various Actions Module messages
"""

import logging
from actions_component import ResilientComponent, ActionMessage
from circuits import Component
from circuits.core.handlers import handler


LOG = logging.getLogger(__name__)


# Some example components to handle various messages

class SampleAction1(ResilientComponent):
    """A sample component that listens on queue `sample`
    for actions from artifacts and from tasks.
    Artifact actions result in various bits of processing.
    Task actions result in an exception (just to show how).

    Note that ResilientComponent is a BaseComponent, which
    does *not* automatically register your methods as event handlers,
    so the handler methods must be decorated with `@handler`.
    See: <http://circuits.readthedocs.org/en/latest/man/handlers.html#explicit-event-handlers>
    """

    channel = "actions.sample"  # Channel name beginning "actions." is a Resilient queue or topic

    # Handle the action named "Artifact Sample"
    @handler("artifact_sample")
    def artifact_sample(self, event, source=None, headers=None, message=None):
        """Action triggered from an artifact onto our queue"""
        LOG.info("SampleAction1 sees: artifact %s", message["artifact"]["value"])
        LOG.debug("Incident id: %s", event.incident["id"])
        LOG.debug("Artifact id: %s", event.artifact["id"])
        # Which action is this?
        LOG.debug("Action id: %s", event.action_id)

        # When calling REST API methods, use the co3_context_token from the event
        ctx = event.context

        # here's a GET/PUT that updates the incident
        def update_func(incident):
            """Called by get/put.  Update the incident and return it."""
            incident["description"] = event.artifact["value"]
            return incident
        uri = "/incidents/{}".format(event.incident["id"])
        incident = self.rest_client().get_put(uri, update_func, co3_context_token=ctx)

        # Yield a string to show in the action status
        yield "ok"

    # Handle the action named "Task Sample"
    @handler("task_sample")
    def task_sample(self, event, source=None, headers=None, message=None):
        """Action triggered from a task onto our queue"""
        # Raise an exception to show the error message in the action status
        raise Exception("An exceptional situation!")


class SampleAction2(Component):
    """A sample component that listens on queue `sample2`."""

    channel = "actions.sample2"  # Channel name beginning "actions." is a Resilient queue or topic

    @handler()
    def _handle_anything(self, event, *args, **kwargs):
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
        # Process the event
        LOG.info("SampleAction2 sees action '%s'", event.displayname)
        yield "done {}".format(event.displayname)


class SampleAction3(Component):
    """An example component where the channel name is set by the caller"""

    def __init__(self, queuename):
        self.channel = "actions." + queuename
        super(SampleAction3, self).__init__()

    def sample_action(self, event, source=None, headers=None, message=None):
        yield "ok"


class SomeOtherComponent(Component):
    """This is just another component, not listening on an Actions channel"""
    channel = "foo"
