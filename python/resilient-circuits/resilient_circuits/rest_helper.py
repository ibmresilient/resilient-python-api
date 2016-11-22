#!/usr/bin/env python

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

"""Global accessor for the Resilient REST API"""

import co3
import os
import sys
import datetime
import json
import logging
import importlib
try:
    # Python 3
    import urllib.parse as urlparse
except:
    # Python 2
    import urlparse
import requests
LOG = logging.getLogger(__name__)
resilient_client = None
connection_opts = None


class LoggingSimpleClient(co3.SimpleClient):
    """ Simple Client version that logs all Resilient Responses """
    def __init__(self, logging_directory="", *args, **kwargs):
        super(LoggingSimpleClient, self).__init__(*args, **kwargs)
        try:
            directory = os.path.expanduser(logging_directory)
            directory = os.path.expandvars(directory)
            assert(os.path.exists(directory))
            self.logging_directory = directory
        except Exception as e:
            raise Exception("Response Logging Directory %s does not exist!", logging_directory)

    def _log_response(self, response, *args, **kwargs):
        """ Log Headers and JSON from a Requests Response object """
        url = urlparse.urlparse(response.url)
        filename = "_".join((str(response.status_code), "{0}", url.path, url.params,
                             datetime.datetime.now().isoformat())).replace('/', '_')
        with open(os.path.join(self.logging_directory, filename.format("JSON")), "w+") as logfile:
            logfile.write(json.dumps(response.json(), indent=2))
        with open(os.path.join(self.logging_directory, filename.format("HEADER")), "w+") as logfile:
            logfile.write(json.dumps(dict(response.headers), indent=2))

    def _connect(self, *args, **kwargs):
        """ Connect to Resilient and log response """
        normal_post = self.session.post
        self.session.post = lambda *args, **kwargs: normal_post(hooks=dict(response=self._log_response), *args, **kwargs)
        session = super(LoggingSimpleClient, self)._connect(*args, **kwargs)
        self.session.post = normal_post
        return session

    def _execute_request(self, operation, url, **kwargs):
        """Execute a HTTP request and log response.
           If unauthorized (likely due to a session timeout), retry.
        """
        wrapped_operation = lambda url, **kwargs: operation(url, hooks=dict(response=self._log_response), **kwargs)
        return super(LoggingSimpleClient, self)._execute_request(wrapped_operation, url, **kwargs)


def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None

def get_resilient_client(opts):
    """Get a connected instance of SimpleClient for Resilient REST API"""
    global resilient_client
    global connection_opts

    new_opts = (opts.get("cafile"),
                opts.get("org"),
                opts.get("host"),
                opts.get("port"),
                opts.get("proxy"),
                opts.get("email"))
    if new_opts != connection_opts:
        resilient_client = None
        connection_opts = new_opts
    if resilient_client:
        return resilient_client

    # Allow explicit setting "do not verify certificates"
    verify = opts.get("cafile")
    if verify == "false":
        LOG.warn("Unverified HTTPS requests (cafile=false).")
        requests.packages.urllib3.disable_warnings()  # otherwise things get very noisy
        verify = False

    # Create SimpleClient for a REST connection to the Resilient services
    url = "https://{0}:{1}".format(opts.get("host", ""), opts.get("port", 443))
    client_args = {"org_name": opts.get("org"),
                   "proxies": opts.get("proxy"),
                   "base_url": url,
                   "verify": verify
                   }
    if opts.get("log_http_responses"):
        LOG.warn("Logging all HTTP Responses from Resilient to %s",
                 opts["log_http_responses"])
        simple_client = LoggingSimpleClient
        client_args["logging_directory"] = opts["log_http_responses"]
    else:
        simple_client = co3.SimpleClient

    resilient_client = simple_client(**client_args)

    if opts.get("resilient_mock"):
        # Use a Mock for the Resilient Rest API
        LOG.warn("Using Mock %s for Resilent REST API", opts["resilient_mock"])
        module_path, class_name =opts["resilient_mock"].rsplit('.', 1)
        path, module_name = os.path.split(module_path)
        sys.path.insert(0, path)
        module = importlib.import_module(module_name)
        LOG.info("Looking for %s in %s", class_name, dir(module))
        mock_class = getattr(module, class_name)
        res_mock = mock_class(org_name=opts.get("org"),
                              email=opts["email"])
        resilient_client.session.mount("https://", res_mock.adapter)

    userinfo = resilient_client.connect(opts["email"], opts["password"])

    # Validate the org, and store org_id in the opts dictionary
    LOG.debug(json.dumps(userinfo, indent=2))
    if(len(userinfo["orgs"])) > 1 and opts.get("org") is None:
        raise Exception("User is a member of multiple organizations; please specify one.")
    if(len(userinfo["orgs"])) > 1:
        for org in userinfo["orgs"]:
            if org["name"] == opts.get("org"):
                opts["org_id"] = org["id"]
    else:
        opts["org_id"] = userinfo["orgs"][0]["id"]

    # Check if action module is enabled and store to opts dictionary
    org_data = resilient_client.get('')
    resilient_client.actions_enabled = org_data["actions_framework_enabled"]


    return resilient_client
