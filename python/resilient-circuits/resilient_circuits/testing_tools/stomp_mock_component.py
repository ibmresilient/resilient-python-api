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

"""Action Module circuits component to mock Resilient stomp server for testing"""

from __future__ import print_function
from circuits import Component, Event, ipc, handler
import logging
import coilmq.start
LOG = logging.getLogger(__name__)

DATA_SECTION = 'resilient'


class run_stomp_server(Event):
    """ Trigger stomp server to start up """
    pass


class ResilientStompMock(Component):
    """ Mock the stomp connection for testing"""
    
    def __init__(self, opts):
        super(ResilientStompMock, self).__init__(opts)
        self.options = opts
        self.process, self.bridge = StompServer(opts).start(process=True, link=self)
        self.fire(ipc(run_stomp_server(), self.bridge.channel))
        LOG.info("fired stomp server start event")

class StompServer(Component):
    def __init__(self, options):
        super(StompServer, self).__init__()
        self.options = options
        self.config_file = self.options["stomp_mock"]
        self.configure(self.options["email"],
                       self.options["password"])

    def run_stomp_server(self):
        print("Starting coilmq serverwith config file %s", self.config_file)
        coilmq.start._main(config=self.config_file)

    def configure(self, username, password):
        """ Set username and password in auth file """
        pass
