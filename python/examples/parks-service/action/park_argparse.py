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

"""Parser for commandline arguments and config properties"""

import co3

class ParkOpts(dict):
    """A dictionary of the commandline options"""
    def __init__(self, config, dictionary):
        super(ParkOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)

class ParkArgumentParser(co3.ArgumentParser):
    """Helper to parse command line arguments."""

    DEFAULT_STOMP_PORT = 65001

    def __init__(self):
        super(ParkArgumentParser, self).__init__(config_file="park.config")

        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        default_queue = self.getopt("resilient", "queue")

        default_park_url = self.getopt("park", "url")

        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")

        self.add_argument("--queue",
                          default=default_queue,
                          help="Message destination API name")

        self.add_argument("--park",
                          default=default_park_url,
                          help="Parks Service URL")

    def parse_args(self, args=None, namespace=None):
        args = super(ParkArgumentParser, self).parse_args(args, namespace)
        return ParkOpts(self.config, vars(args))
