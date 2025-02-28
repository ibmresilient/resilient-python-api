# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

try:
    from importlib.metadata import distribution, PackageNotFoundError
except ImportError:
    from importlib_metadata import distribution, PackageNotFoundError
try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    __version__ = None

from .actions_component import ResilientComponent
from .action_message import ActionMessageBase, ActionMessage, \
    FunctionMessage, FunctionResult, FunctionError, \
    StatusMessage, BaseFunctionError, LowCodeMessage, LowCodeResult
from .decorators import function, inbound_app, app_function, low_code_function, handler, required_field, required_action_field, defer, debounce
from .actions_test_component import SubmitTestAction, SubmitTestFunction, SubmitTestInboundApp, SubmitTestLowCodeApp
from .app_function_component import AppFunctionComponent
from .helpers import is_this_a_selftest
