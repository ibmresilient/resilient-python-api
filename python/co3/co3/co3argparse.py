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

"""Command-line argument parser for Resilient apps"""

import os
import sys
import argparse
import getpass
if sys.version_info.major == 2:
    from co3 import ensure_unicode
else:
    from co3.co3 import ensure_unicode
import logging
try:
    # For all python < 3.2
    import backports.configparser as configparser
except ImportError:
    import configparser

logger = logging.getLogger(__name__)


class ArgumentParser(argparse.ArgumentParser):
    """Helper to parse common Resilient command line arguments.

    Optionally, arguments can be specified in a config file, section '[resilient]'.

    It is expected that a command line utility that needs to work with a Resilient
    server will create its own class that inherits this class.  Its __init__
    method will call self.add_argument as necessary.

    See https://docs.python.org/3/library/argparse.html for more details.
    """

    DEFAULT_PORT = 443
    config = None

    def getopt(self, section, opt):
        """Get a single option value, or None if not present"""
        if self.config:
            if opt in self.config.options(section):
                return self.config.get(section, opt)
        return None

    def getopts(self, section, opt):
        """Get an array of option values, or [] if not present"""
        if self.config:
            if opt in self.config.options(section):
                return self.config.get(section, opt).split(u",")
        return []

    def __init__(self, config_file=None):
        super(ArgumentParser, self).__init__()

        # Read configuration options.
        if config_file:
            config_path = ensure_unicode(config_file)
            config_path = os.path.expanduser(config_path)
            if os.path.exists(config_path):
                try:
                    self.config = configparser.ConfigParser()
                    with open(config_path, 'r', encoding='utf-8') as f:
                        first_byte = f.read(1)
                        if first_byte != u'\ufeff':
                            # Not a BOM, no need to skip first byte
                            f.seek(0)
                        self.config.read_file(f)
                except Exception as exc:
                    logger.warn(u"Couldn't read config file '%s': %s", config_path, exc)
                    self.config = None
            else:
                logger.warn(u"Couldn't read config file '%s'", config_file)

        default_email = self.getopt("resilient", "email")
        default_password = self.getopt("resilient", "password")
        default_host = self.getopt("resilient", "host")
        default_port = self.getopt("resilient", "port") or self.DEFAULT_PORT
        default_proxy = self.getopts("resilient", "proxy")
        default_org = self.getopt("resilient", "org")
        default_cafile = self.getopt("resilient", "cafile")

        self.add_argument("--email",
                          default=default_email,
                          required=default_email is None,
                          help="The email address to use to authenticate to the Resilient server.")

        self.add_argument("--password",
                          default=default_password,
                          help="WARNING:  This is an insecure option since the password "
                               "will be visible to other processes and stored in the "
                               "command history.  The password to use to authenticate "
                               "to the Resilient server.  If omitted, the you will be prompted.")

        self.add_argument("--host",
                          default=default_host,
                          required=default_host is None,
                          help="Resilient server host name.")

        self.add_argument("--port",
                          type=int,
                          default=default_port,
                          help="Resilient server REST API port number.")

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
        

    def parse_args(self, args=None, namespace=None):
        args = super(ArgumentParser, self).parse_args(args, namespace)

        password = args.password
        while not password:
            password = getpass.getpass()
        args.password = ensure_unicode(password)

        if args.cafile:
            args.cafile = os.path.expanduser(args.cafile)

        return args
