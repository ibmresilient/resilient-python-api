# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

import pkg_resources
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    pass

from .misc import verify_subset
from .mocks import BasicResilientMock, resilient_endpoint
from .circuits_fixtures import call_event, call_event_from_name, wait_for
