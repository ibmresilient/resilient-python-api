""" py.test plugin configuration for pytest-resilient-circuits """

_help_email = "Resilient user email"
_help_host = "Resilient host"
_help_password = "Resilient password"
_help_org = "Resilient org"

def pytest_addoption(parser):
    """ Configuration Options """
    parser.addini(name = 'resilient_email',
                  help = _help_email,
                  default = '')

    parser.addini(name = 'resilient_host',
                  help = _help_host,
                  default = '')

    parser.addini(name = 'resilient_password',
                  help = _help_password,
                  default = '')

    parser.addini(name = 'resilient_org',
                  help = _help_org,
                  default = '')

from circuits_fixtures import *
from resilient_circuits_fixtures import *
