# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" py.test plugin configuration for pytest-resilient-circuits """

_help_email = "Resilient user email"
_help_host = "Resilient host"
_help_password = "Resilient password"
_help_org = "Resilient org"

def pytest_addoption(parser):
    """ Configuration Options """
    parser.addoption("--resilient_email",
                     help=_help_email,
                     action="store",
                     default="",
                     required=False)

    parser.addoption("--resilient_host",
                     help=_help_host,
                     action="store",
                     default="",
                     required=False)

    parser.addoption("--resilient_password",
                     help=_help_password,
                     action="store",
                     default="",
                     required=False)

    parser.addoption("--resilient_org",
                     help=_help_org,
                     action="store",
                     default="",
                     required=False)

from pytest_resilient_circuits.circuits_fixtures import *
from pytest_resilient_circuits.resilient_circuits_fixtures import *

