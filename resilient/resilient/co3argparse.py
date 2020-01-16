# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Command-line argument parser for Resilient apps"""

import os
import sys
import argparse
import getpass
import keyring
import logging
from six import string_types

if sys.version_info.major == 2:
    from io import open
    from resilient import ensure_unicode, get_proxy_dict, get_resilient_circuits_version
else:
    from resilient.co3 import ensure_unicode, get_proxy_dict, get_resilient_circuits_version

try:
    # For all python < 3.2
    import backports.configparser as configparser
except ImportError:
    import configparser

logger = logging.getLogger(__name__)


class ConfigDict(dict):
    """A dictionary, with property-based accessor

    >>> opts = {"one": 1}
    >>> cd = ConfigDict(opts)
    >>> cd["one"]
    1
    >>> cd.one
    1

    """
    def __getattr__(self, name):
        """Attributes are made accessible as properties"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError()


class ArgumentParser(argparse.ArgumentParser):
    """Helper to parse common Resilient command line arguments.

    Optionally, arguments can be specified in a config file, section :samp:`[resilient]`.

    It is expected that a command line utility that needs to work with a Resilient
    server will create its own class that inherits this class.  Its `__init__`
    method should call :samp:`self.add_argument(...)` as necessary.

    See https://docs.python.org/3/library/argparse.html for more details.
    """

    DEFAULT_PORT = 443
    config = None

    def getopt(self, section, opt):
        """Get a single option value.

        :param section: The configuration section.
        :param opt: The configuration option.
        :return: The value, or None if not present.
        """
        if self.config:
            if opt in self.config.options(section):
                return self.config.get(section, opt)
        return None

    def getopts(self, section, opt):
        """Get a comma-separated option value as an array.

        :param section: The configuration section.
        :param opt: The configuration option.
        :return: The value, or [] if not present.
        """
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
                    self.config = configparser.ConfigParser(interpolation=None)
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
        default_key_id = self.getopt("resilient", "api_key_id")
        default_key_secret = self.getopt("resilient", "api_key_secret")
        default_host = self.getopt("resilient", "host")
        default_port = self.getopt("resilient", "port") or self.DEFAULT_PORT
        default_proxy = self.getopts("resilient", "proxy")
        default_org = self.getopt("resilient", "org")
        default_cafile = self.getopt("resilient", "cafile")
        default_cache_ttl = int(self.getopt("resilient", "cache_ttl") or 0)
        default_proxy_host = self.getopt("resilient", "proxy_host")
        default_proxy_port = self.getopt("resilient", "proxy_port") or 0
        default_proxy_user = self.getopt("resilient", "proxy_user")
        default_proxy_password = self.getopt("resilient", "proxy_password")
        default_stomp_prefetch_limit = int(self.getopt("resilient", "stomp_prefetch_limit") or 20)
        default_resilient_mock = self.getopt("resilient", "resilient_mock")

        self.add_argument("--email",
                          default=default_email,
                          help="The email address to use to authenticate to the Resilient server.")

        self.add_argument("--password",
                          default=default_password,
                          help="WARNING:  This is an insecure option since the password "
                               "will be visible to other processes and stored in the "
                               "command history.  The password to use to authenticate "
                               "to the Resilient server.  If omitted, the you will be prompted.")

        self.add_argument("--api_key_id",
                          default=default_key_id,
                          help="The api key id for API key.")

        self.add_argument("--api_key_secret",
                          default=default_key_secret,
                          help="WARNING:  This is an insecure option since the key secret "
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

        self.add_argument("--cache-ttl",
                          default=default_cache_ttl or 240,
                          type=int,
                          help="TTL for API responses when using cached_get")

        self.add_argument("--proxy_host",
                          default=default_proxy_host,
                          help="HTTP Proxy host for Resilient Connection.")

        self.add_argument("--proxy_port",
                          type=int,
                          default=default_proxy_port,
                          help="HTTP Proxy port for Resilient Connection.")

        self.add_argument("--proxy_user",
                          default=default_proxy_user,
                          help="HTTP Proxy username for Resilient connection authentication.")

        self.add_argument("--proxy_password",
                          default=default_proxy_password,
                          help="HTTP Proxy password for Resilient connection authentication.")

        self.add_argument("--stomp-prefetch-limit",
                          default=default_stomp_prefetch_limit,
                          type=int,
                          help="MAX number of Action Module messages to send before ACK is required")

        v_resc = get_resilient_circuits_version()

        # Having --resilient-mock here allows us to run unit tests for resilient-circuits and resilient-sdk
        # This argument will be added if:
        # - resilient-circuits is not installed
        # - resilient-circuits is installed and is > 34
        if not v_resc or (v_resc and v_resc.get("major") > 34):
            self.add_argument("--resilient-mock",
                            default=default_resilient_mock, 
                            help="<path_to_mock_module>.NameOfMockClass")

    def parse_args(self, args=None, namespace=None):
        """
        Parse the configuration options and command-line arguments.

        :return: Note: the return value is a dict, not a Namespace.
        """
        # (the implementation calls parse_known_args)
        args = super(ArgumentParser, self).parse_args(args, namespace)
        return args

    def parse_known_args(self, args=None, namespace=None):
        """
        Parse the configuration options and command-line arguments.

        :return: Note: the return value is a dict, not a Namespace.
        """
        # Parse the known arguments
        args, argv = super(ArgumentParser, self).parse_known_args(args, namespace)
        return _post_process_args(args), argv


def _post_process_args(args):
    # Post-process any options that reference keyring or environment variables
    opts = parse_parameters(vars(args))
    args = ConfigDict(opts)

    # Post-processing for other special options
    password = args.password
    email = args.email

    while (not password and email) and (not args.get("no_prompt_password")):
        password = getpass.getpass()
    args["password"] = ensure_unicode(password)

    if args.get("cafile"):
        args["cafile"] = os.path.expanduser(args.cafile)

    if args.get("stomp_cafile"):
        args["stomp_cafile"] = os.path.expanduser(args.stomp_cafile)

    if args.get("proxy_host"):
        args["proxy"] = get_proxy_dict(args)

    return args


def parse_parameters(options):
    """Given a dict that has configuration keys mapped to values,
       - If a value begins with '^', redirect to fetch the value from
         the secret key stored in the keyring.
         The keyring service name is always just an underscore
         (so keys must be unique in the whole options dict)
       - If a value begins with '$', fetch the value from environment.

    >>> opts = {
    ...    "thing": u"value",
    ...    "key3": "^val3",
    ...    "key4": u"$val4",
    ...    "key5": "$val5",
    ...    "deep1": {"key1": "val1", "key2": u"^val2"}
    ... }

    >>> keyring.set_password("_", "val3", "key3password")
    >>> keyring.set_password("_", "val2", "")
    >>> keyring.set_password("deep1", "val2", "key2password")
    >>> os.environ["val4"] = "key4param"
    >>> os.environ["val5"] = "key5param"

    >>> str(parse_parameters(opts)["key3"])
    'key3password'

    >>> parse_parameters(opts)["deep1"]["key1"]
    'val1'

    >>> str(parse_parameters(opts)["deep1"]["key2"])
    'key2password'

    >>> parse_parameters(opts)["deep1"]["key1"]
    'val1'

    >>> parse_parameters(opts)["key4"]
    'key4param'

    >>> parse_parameters(opts)["key5"]
    'key5param'

    """
    names = ()
    return _parse_parameters(names, options)


def _parse_parameters(names, options):
    """Parse parameters, with a tuple of names for keyring context"""
    for key in options.keys():
        val = options[key]
        if isinstance(val, dict):
            val = _parse_parameters(names + (key,), val)
        if isinstance(val, string_types) and len(val) > 1 and val[0] == "^":
            # Decode a secret from the keystore
            val = val[1:]
            service = ".".join(names) or "_"
            if service == "resilient":
                # Special case, becuase of the way we parse commandlines, treat this as root
                service = "_"
            logger.debug("keyring get('%s', '%s')", service, val)
            val = keyring.get_password(service, val)
        if isinstance(val, string_types) and len(val) > 1 and val[0] == "$":
            # Read a value from the environment
            val = val[1:]
            logger.debug("env('%s')", val)
            val = os.environ.get(val)
        options[key] = val
    return options
