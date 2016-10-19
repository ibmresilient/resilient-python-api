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
    def mark( func ):
        func.uri = uri
        func.request_type = request_type
        return func
    return mark

class ResilientMockBase(object):
    class __metaclass__(type):
        """ creates collection of with a `uri` attribute
            and stores it on the class as `registered_endpoints`
        """
        def __new__(cls, name, bases, attr):
            Endpoint = namedtuple("Endpoint", "type callback")
            endpoints = {}
            for obj in attr.itervalues():
                    if hasattr(obj, 'uri'):
                        endpoints[obj.uri] = Endpoint(type=obj.request_type,
                                                      callback=obj)
            attr['registered_endpoints'] = endpoints
            return type.__new__(cls, name, bases, attr)


class ResilientMock(ResilientMockBase):
    """ Base class for creating Resilient Rest API Mock definitions """
    def __init__(self, org_name=None, email=None):
        LOG.info("Initialize ResilientMock")
        self.email = email or "api@example.com"
        self.org_name = org_name or "Test Org"

        self.adapter = requests_mock.Adapter()
        for uri, handler in self.registered_endpoints.items():
            # Register with regex since some endpoints embed the org_id in the path
            LOG.info("Registering %s %s to %s", handler.type, uri, str(handler.callback))
            callback = handler.callback
            self.adapter.add_matcher(lambda request,
                                     method=handler.type,
                                     callback=callback,
                                     uri=uri: self._custom_matcher(method,
                                                                   uri,
                                                                   lambda request: callback(self, request),
                                                                   request))
    @staticmethod
    def _custom_matcher(request_type, uri, response_callback, request):
        """ matcher function for passing to adapter.add_matcher() """
        LOG.debug("Comparing %s to %s. Regex Search %s in %s", request.method,
                  request_type, uri, request.url)
        if request.method == request_type and re.search(uri, request.url):
            LOG.debug("Match!")
            return response_callback(request)
        else:
            LOG.debug("Does not match.")
            return None
