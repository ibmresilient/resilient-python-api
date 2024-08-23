# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

try:
    from importlib.metadata import distribution, PackageNotFoundError
except ImportError:
    from importlib_metadata import distribution, PackageNotFoundError
try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    __version__ = None

from .misc import verify_subset
from .mocks import BasicResilientMock, BasicResilientMockNoRegisterLog, resilient_endpoint
from .circuits_fixtures import call_event, call_event_from_name, wait_for
