"""Command-line argument parser for Resilient apps"""

import os
import sys
import argparse
import getpass
import logging
if sys.version_info[0] < 3:
    import ConfigParser as configparser
else:
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
                return self.config.get(section, opt).split(",")
        return []

    def __init__(self, config_file=None):
        super(ArgumentParser, self).__init__()

        # Read configuration options.
        if config_file:
            config_path = os.path.expanduser(config_file)
            if os.path.exists(config_path):
                try:
                    self.config = configparser.SafeConfigParser()
                    self.config.read(config_path)
                except Exception as exc:
                    logger.warn("Couldn't read config file '%s': %s", config_path, exc)
                    self.config = None
            else:
                logger.warn("Couldn't read config file '%s'", config_path)

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
        args.password = password

        if args.cafile:
            args.cafile = os.path.expanduser(args.cafile)

        return args
