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

"""Argument parse helper, for values stored in keyring or file"""

import co3
import getpass
import os
import keyring
import logging


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
         the secret key stored in the keyring.  The keyring service name is
         the parent key (or keys, dotted-joined).

    >>> opts = {
    ...    "thing": "value",
    ...    "key3": "^val3",
    ...    "deep1": {"key1": "val1", "key2": "^val2"}
    ... }

    >>> keyring.set_password("_", "val3", "key3password")
    >>> parse_parameters(opts)["key3"]
    u'key3password'

    >>> keyring.set_password("_.deep1", "val2", "key2password")
    >>> parse_parameters(opts)["deep1"]["key2"]
    u'key2password'

    """
    names = ()
    return _parse_parameters(names, options)


def _parse_parameters(names, options):
    """Parse parameters, with a tuple of names for keyring context"""
    for key in options.keys():
        val = options[key]
        if isinstance(val, dict):
            val = _parse_parameters(names + (key,), val)
        if isinstance(val, str) and len(val) > 1 and val[0] == "^":
            # Decode a secret from the keystore
            val = val[1:]
            service = ".".join(names) or "_"
            LOG.debug("keyring get('%s', '%s')", service, val)
            val = keyring.get_password(service, val)
        if isinstance(val, str) and len(val) > 1 and val[0] == "$":
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
