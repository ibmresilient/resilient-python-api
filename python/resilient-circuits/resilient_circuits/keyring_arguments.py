#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Argument parse helper, for values stored in keyring or file"""

import co3
import getpass
import os
import keyring
import logging

try:
    basestring
except NameError:
    # Python 3
    basestring = str

LOG = logging.getLogger(__name__)


class ArgumentParser(co3.ArgumentParser):
    """An argument parser that implements password lookup from keyring"""

    def parse_args(self, args=None, namespace=None, prompt_password=True):
        """Parse arguments, and resolve password-based values from keyring"""
        # Bypass the co3 behavior, go to its super
        args = super(co3.ArgumentParser, self).parse_args(args, namespace)
        opts = parse_parameters(vars(args))
        args = ConfigDict(opts)

        password = args.password
        while (not password) and (not args.no_prompt_password):
            password = getpass.getpass()
        args["password"] = password

        if args.cafile:
            args["cafile"] = os.path.expanduser(args.cafile)

        if args.stomp_cafile:
            args["stomp_cafile"] = os.path.expanduser(args.stomp_cafile)

        return args


class ConfigDict(dict):
    """A dictionary, with property-based accessor"""

    def __getattr__(self, name):
        """Attributes are made accessible as properties"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError()


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
    >>> keyring.set_password("_", "val2", "key2password")
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
        if isinstance(val, basestring) and len(val) > 1 and val[0] == "^":
            # Decode a secret from the keystore
            val = val[1:]
            service = ".".join(names) or "_"
            LOG.debug("keyring get('%s', '%s')", service, val)
            val = keyring.get_password("_", val)
        if isinstance(val, basestring) and len(val) > 1 and val[0] == "$":
            # Read a value from the environment
            val = val[1:]
            LOG.debug("env('%s')", val)
            val = os.environ.get(val)
        options[key] = val
    return options


if __name__ == "__main__":
    import doctest
    logging.basicConfig(level=logging.DEBUG)
    doctest.testmod()
