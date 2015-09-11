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

"""Actions Module server

This example uses the `Circuits <http://circuitsframework.com/>` framework to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

"""

import co3
import logging
from actions_component import Actions
from circuits import Component, Debugger
import sample_components

LOG = logging.getLogger(__name__)


class AppArgumentParser(co3.ArgumentParser):
    """Helper to parse command line arguments."""
    DEFAULT_STOMP_PORT = 65001

    def __init__(self):
        super(AppArgumentParser, self).__init__(config_file="app.config")
        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")

    def parse_args(self, args=None, namespace=None):
        """Parse commandline arguments and construct an opts dictionary"""
        args = super(AppArgumentParser, self).parse_args(args, namespace)
        return vars(args)


# Main component for our application
class App(Component):
    """Our main app component, which sets up the Resilient services"""

    def __init__(self, opts):
        super(App, self).__init__()
        # Connect to events from Actions Module
        Actions(opts).register(self)

    def started(self, event, component):
        """Started Event Handler"""
        LOG.info("App Started")

    def stopped(self, event, component):
        """Stopped Event Handler"""
        LOG.info("App Stopped")


def main():
    """Main demonstration app"""

    # The main app component initializes the Resilient services
    opts = AppArgumentParser().parse_args()
    app = App(opts)

    # Debugger is useful to see all the messages (at DEBUG level)
    Debugger(logger=logging.getLogger("debugger")).register(app)

    # Register all the action handler components

    # SampleAction1 is a ResilientComponent, pass 'opts' to its constructor
    sample_components.SampleAction1(opts).register(app)

    sample_components.SampleAction2().register(app)
    sample_components.SampleAction3("queue3").register(app)

    # If a component is registered, then unregistered, it won't receive messages
    component = sample_components.SampleAction3("unused-queue-name")
    component.register(app)
    component.unregister()

    # If a component is not listening for actions queues, it won't receive their messages
    sample_components.SomeOtherComponent().register(app)

    # Run until interrupted
    app.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("stomp.py").setLevel(logging.WARN)
    main()
