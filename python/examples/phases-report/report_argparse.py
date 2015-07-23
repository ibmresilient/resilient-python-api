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

import sys
import argparse
import getpass
if sys.version_info.major < 3:
    import ConfigParser as configparser
else:
    import configparser
from datetime import datetime


class ReportOpts(dict):
    """A dictionary of the commandline options and all the config 'query' options"""
    def __init__(self, config, dictionary):
        super(ReportOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Date must be YYYY-MM-DD: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

class ReportArgumentParser(argparse.ArgumentParser):
    """Helper to parse command line arguments."""

    DEFAULT_PORT = 443

    def getopt(self, section, opt):
        """Get a single option value, or None if not present"""
        if opt in self.config.options(section):
            return self.config.get(section, opt)
        return None

    def getopts(self, section, opt):
        """Get an array of option values, or [] if not present"""
        if opt in self.config.options(section):
            return self.config.get(section, opt).split(",")
        return []

    def __init__(self, config_file="report.config"):
        super(ReportArgumentParser, self).__init__()

        # Read configuration options.
        self.config = configparser.SafeConfigParser()
        self.config.read(config_file)

        default_user = self.getopt("resilient", "user")
        default_password = self.getopt("resilient", "password")
        default_host = self.getopt("resilient", "host")
        default_port = self.getopt("resilient", "port") or self.DEFAULT_PORT
        default_proxy = self.getopts("resilient", "proxy")
        default_org = self.getopt("resilient", "org")
        default_cafile = self.getopt("resilient", "cafile")

        self.add_argument("--user",
                          default=default_user,
                          required=default_user is None,
                          help="The email address to use to authenticate to the Resilient server.")

        self.add_argument("--password",
                          default=default_password,
                          help="The password to use to authenticate to the Resilient server."
                               "If omitted, the you will be prompted.")

        self.add_argument("--host",
                          default=default_host,
                          required=default_host is None,
                          help="Resilient server host name")

        self.add_argument("--port",
                          type=int,
                          default=default_port,
                          help="Resilient server REST API port number")

        self.add_argument("--proxy",
                          default=default_proxy,
                          nargs="*",
                          help="An optional HTTP proxy to use when connecting.")

        self.add_argument("--org",
                          default=default_org,
                          help="The name of the organization to use.  If you are a member "
                               "of just one organization, then you can omit this argument.")

        self.add_argument("--cafile",
                          default=default_cafile,
                          help="The name of a file that contains trusted certificates.")

        self.add_argument("--since",
                          type=valid_date,
                          help="Only report incidents created since this date (YYYY-MM-DD)")


    def parse_args(self, args=None, namespace=None):
        args = super(ReportArgumentParser, self).parse_args(args, namespace)

        password = args.password
        while not password:
            password = getpass.getpass("Resilient password for {}: ".format(args.user))
        args.password = password

        return ReportOpts(self.config, vars(args))
