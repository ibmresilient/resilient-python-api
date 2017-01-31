""" Requests mock for Resilient REST API """

import logging
from collections import namedtuple
import json
import re
import requests_mock
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.DEBUG)


def resilient_endpoint(request_type, uri):
    def mark(func):
        func.uri = uri
        func.request_type = request_type
        return func
    return mark


class ResilientMockBase(object):
    class __metaclass__(type):
        """ creates collection with a `uri` attribute
            and stores it on the class as `registered_endpoints`
        """
        def __new__(cls, name, bases, attr):
            Endpoint = namedtuple("Endpoint", "type uri")
            endpoints = {}
            for obj in attr.itervalues():
                    if hasattr(obj, 'uri'):
                        endpoints[Endpoint(type=obj.request_type, uri=obj.uri)] = obj
            attr['registered_endpoints'] = endpoints
            return type.__new__(cls, name, bases, attr)


class ResilientMock(ResilientMockBase):
    """ Base class for creating Resilient Rest API Mock definitions """
    def __init__(self, org_name=None, email=None):
        self.email = email or "api@example.com"
        self.org_name = org_name or "Test Org"
        LOG.info("Initialize ResilientMock %s %s", self.email, self.org_name)
        
        self.adapter = requests_mock.Adapter()
        for endpoint, handler in self.registered_endpoints.items():
            # Register with regex since some endpoints embed the org_id in the path
            LOG.info("Registering %s %s to %s", endpoint.type,
                     endpoint.uri, str(handler))
            self.adapter.add_matcher(lambda request,
                                     method=endpoint.type,
                                     callback=handler,
                                     uri=endpoint.uri: self._custom_matcher(method,
                                                                   uri,
                                                                   lambda request: callback(self, request),
                                                                   request))

    @staticmethod
    def _custom_matcher(request_type, uri, response_callback, request):
        """ matcher function for passing to adapter.add_matcher() """
        if request.method == request_type and re.search(uri, request.url):
            return response_callback(request)
        else:
            return None
