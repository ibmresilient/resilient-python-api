#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

"""
Resilient utility to configure secrets in the config file (~/.resilient/app.config)
"""

from __future__ import print_function
import sys
import os
import logging
import keyring
import resilient
from six import string_types

try:
    # For all python < 3.2
    from io import open
    import backports.configparser as configparser
except ImportError:
    import configparser


logger = logging.getLogger(__name__)
logging.basicConfig()


# Main class for util script
class KeyringUtils(object):
    """Our main app class"""

    def __init__(self):
        super(KeyringUtils, self).__init__()

        config_file = resilient.get_config_file()
        print(u"Configuration file: {}".format(config_file))

        # Read configuration options.
        if config_file:
            config_path = resilient.ensure_unicode(config_file)
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
        else:
            logger.warn(u"Couldn't read config file")

    def run(self):
        """
        Read the configuration file
        For any 'keyring'-based parameters: prompt the user to set or edit the value.
        """
        opts = {"__any_secrets__": False}
        for section in self.config.sections():
            items = dict((item.lower(), self.config.get(section, item)) for item in self.config.options(section))
            items["__any_secrets__"] = False
            opts.update({section: items})

        print(u"Secrets are stored with '{}'".format(type(keyring.get_keyring()).__module__))
        try:
            self.list_parameters(opts)
        except (KeyboardInterrupt, EOFError):
            print()

        if opts.get("__any_secrets__"):
            print(u"Done.")
        else:
            print(u"Nothing to do.")

    @staticmethod
    def list_parameters(options):
        """
        Process all sections in the config 'options' dictionary
        """
        names = ()
        return _list_parameters(names, options)


def get_input(prompt):
    if sys.version_info[0] >= 3:
        return input(prompt)
    value = raw_input(prompt)
    return value.decode(sys.stdin.encoding)


def _list_parameters(names, options):
    """
    Parse parameters, with a tuple of names for keyring context.

    Given a dict that has configuration keys mapped to values,
       - If a value begins with '^', redirect to fetch the value from
         the secret key stored in the keyring.
         The keyring service name is always just an underscore
         (so keys must be unique in the whole options dict)

    """
    for key in options.keys():
        val = options[key]
        if isinstance(val, dict):
            val = _list_parameters(names + (key,), val)
            options["__any_secrets__"] = options["__any_secrets__"] or val["__any_secrets__"]
        if isinstance(val, string_types) and len(val) > 1 and val[0] == "^":
            # This value is from the keyring
            options["__any_secrets__"] = True
            tag = val
            val = val[1:]
            service = ".".join(names) or "_"
            if service == "resilient":
                # Special case, becuase of the way we parse commandlines, treat this as root
                service = "_"
            logger.debug("keyring get('%s', '%s')", service, val)
            value = keyring.get_password(service, val)

            if value is None:
                print("[{0}] {1}: <not set>".format(".".join(names) or "_", key))
            else:
                print("[{0}] {1}: {2}".format(".".join(names) or "_", key, tag))

            newvalue = None
            do_set = True
            while do_set:
                newvalue = get_input(u"  Enter new value (or <ENTER> to leave unchanged): ")
                if len(newvalue) == 0:
                    do_set = False
                    break
                confirm = get_input(u"  Confirm new value: ")
                if confirm == newvalue:
                    break
                print(u"Values do not match, try again.")

            if do_set:
                keyring.set_password(service, val, newvalue)
                print(u"Value set.")

        options[key] = val
    return options


def main():
    KeyringUtils().run()


if __name__ == "__main__":
    main()
