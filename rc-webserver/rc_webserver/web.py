# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Our decorator for web service methods"""

import json
import logging
import sys
from functools import update_wrapper
if sys.version_info.major < 3:
    JSONDecodeError = ValueError
    from inspect import getargspec
else:
    from json import JSONDecodeError
    from inspect import getfullargspec


from circuits.core import handler
from circuits.web.wrappers import Response
from circuits.web.exceptions import HTTPException
from circuits.web.errors import httperror
import circuits.six as six


LOG = logging.getLogger(__name__)


def exposeWeb(*channels, **config):
    """
    A decorator that identifies your Circuits function as a Web service endpoint.

    :param channels: A path/fragment to handle calls that begin with that path.  A path of "index" is the
        handler for the "root document" or empty path.  Paths are all relative to `self.channel`.
        Alternatively, a HTTP verb ("GET", "POST", etc.) to handle all incoming events with that verb;
    :param config: Optional (ignored)
    :return: Dictionary that should be returned as JSON by the web service.

    Your class should inherit from :class:`circuits.web.BaseController`, and may additionally
    inherit from :class:`resilient_circuits.ResilientComponent` to handle action and access the Resilient REST API.

    For example, to handle a specific path for a REST method:

    .. code-block:: python

        class WebExample(BaseController, ResilientComponent):

            def __init__(self, opts):
                super(WebExample, self).__init__(opts)
                # 'self.channel' declares the topmost path that will be handled in this class.
                self.channel = "/example"

            @exposeWeb("incident")
            def _create_note(self, event, *args, **kwargs):
                # Handle POST to /example/incident/<inc_id>/note
                request = event.args[0]
                response = event.args[1]
                if request.method != "POST":
                    raise MethodNotAllowed(request.method)
                response.status = 200
                return {"status":"OK"}

    To handle requests for the index (root) path:

    .. code-block:: python

        @exposeWeb("index")
        def _index_request(self, event, *args, **kwargs):
            # handle any request for the root ("/")
            pass

    A generic handler that sends all POST requests to one function:

    .. code-block:: python

        @exposeWeb("POST")
        def _post_request(self, event, *args, **kwargs):
            # handle any POST
            pass

    """
    def decorate(f):
        @handler(*channels, **config)
        def wrapper(self, event, *args, **kwargs):
            try:
                if not hasattr(self, "request"):
                    (self.request, self.response), args = args[:2], args[2:]
                    self.request.args = args
                    self.request.kwargs = kwargs
                    self.cookie = self.request.cookie
                    if hasattr(self.request, "session"):
                        self.session = self.request.session

                if hasattr(self, "_auth"):
                    self._auth()

                if not getattr(f, "event", False):
                    result = f(self, *args, **kwargs)
                else:
                    result = f(self, event, *args, **kwargs)

                if (isinstance(result, httperror)
                        or isinstance(result, Response)
                        or isinstance(result, six.string_types)):
                    return result

                if result is None:
                    self.response.status = 204
                    return ""
                else:
                    try:
                        self.response.headers["Content-Type"] = "application/json; charset=utf-8"
                        return json.dumps(result)
                    except (JSONDecodeError, TypeError) as e:
                        return httperror(self.request, self.response, code=500,
                                         description="JSON decode failed for object of type '%s'" % type(result))
            except HTTPException as e:
                LOG.exception(e)
                return httperror(self.request, self.response, code=e.code, description=e.description)
            except Exception as e:
                LOG.exception(e)
                msg = getattr(e, 'message', repr(e))
                return httperror(self.request, self.response, code=500, description=msg)
            finally:
                if hasattr(self, "request"):
                    del self.request
                    del self.response
                    del self.cookie
                if hasattr(self, "session"):
                    del self.session

        if sys.version_info.major < 3:
            wrapper.args, wrapper.varargs, wrapper.varkw, wrapper.defaults = \
                getargspec(f)
        else:
            #python 3 (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations)
            wrapper.args, wrapper.varargs, wrapper.varkw, wrapper.defaults, _, _, _ = \
                getfullargspec(f)

        if wrapper.args and wrapper.args[0] == "self":
            del wrapper.args[0]

        if wrapper.args and wrapper.args[0] == "event":
            f.event = True
            del wrapper.args[0]
        wrapper.event = True

        return update_wrapper(wrapper, f)

    return decorate
