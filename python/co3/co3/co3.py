# Co3 Systems, Inc. ("Co3") is willing to license software or access to 
# software to the company or entity that will be using or accessing the 
# software and documentation and that you represent as an employee or 
# authorized agent ("you" or "your" only on the condition that you 
# accept all of the terms of this license agreement.
#
# The software and documentation within Co3's Development Kit are 
# copyrighted by and contain confidential information of Co3. By 
# accessing and/or using this software and documentation, you agree 
# that while you may make derivative works of them, you:
#
# 1)   will not use the software and documentation or any derivative 
#      works for anything but your internal business purposes in 
#      conjunction your licensed used of Co3's software, nor
# 2)   provide or disclose the software and documentation or any 
#      derivative works to any third party.
# 
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
# OF THE POSSIBILITY OF SUCH DAMAGE.

import requests 
import json
import sys
import traceback
import ssl

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

class TLSHttpAdapter(HTTPAdapter):
    """Adapter that ensures that we use TLSv1 (some Pythons default to SSLv3)."""
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

class SimpleHTTPException(Exception):
    """Exception for HTTP errors."""
    def __init__(self, response):
        """
        Args:
          response - the Response object from the get/put/etc.
        """
        super(SimpleHTTPException, self).__init__(response.reason)

        self.response = response

class SimpleClient:
    """Helper for using Co3 REST API."""

    headers = {'content-type': 'application/json'}
    cookies = None
    org_id = None
    org_name = None
    base_url = 'https://app.co3sys.com'
    verify = True
    proxies = None
    session = None

    def __init__(self, org_name = None, base_url = None, proxies = None, verify = None):
        """
        Args:
          org_name - the name of the organization to use.
          base_url - the base URL to use.
          proxies - HTTP proxies to use, if any.
          verify - The name of a PEM file to use as the list of trusted CAs.
        """
        self.org_name = org_name
        self.proxies = proxies
        if base_url:
            self.base_url = base_url
        if verify != None:
            self.verify = verify
        self.session = requests.Session()
        self.session.mount('https://', TLSHttpAdapter())

    def connect(self, email, password):
        """Performs connection, which includes authentication.

        Args:
          email - the email address to use for authentication.
          password - the password
        Returns:
          The Co3 session object (dict)
        Raises:
          SimpleHTTPException - if an HTTP exception occurrs.
        """

        data = { 
            'email' : email,
            'password' : password
        } 

        response = self.session.post("{}/rest/session".format(self.base_url), 
            proxies=self.proxies, 
            data=json.dumps(data), 
            verify=self.verify, 
            headers=self.__make_headers()) 

        self._raise_if_error(response)

        session = json.loads(response.text)

        orgs = session['orgs']

        if orgs is None or len(orgs) == 0:
            raise Exception("User is a member of no orgs")
        elif self.org_name:
            org_names = []

            for org in orgs:
                org_name = org['name']

                org_names.append(org_name)

                if org_name == self.org_name:
                    self.org_id = org['id']

            if self.org_id is None:
                raise Exception("User is not a member of the organization {}; orgs = {}".format(self.org_name, ','.join(org_names)))
        else:
            # No org_name specified...use the first one that is returned.
            self.org_id = orgs[0]['id']

        # set the X-sess-id token, which is used to prevent CSRF attacks.
        self.headers['X-sess-id'] = session['csrf_token']
        self.cookies = {
            'JSESSIONID': response.cookies['JSESSIONID']
        }
        return session

    def __make_headers(self, co3_context_token = None):
        """Makes a headers dict, including the X-Co3ContextToken (if co3_context_token is specified)."""
        headers = self.headers.copy()
        if co3_context_token is not None:
            headers['X-Co3ContextToken'] = co3_context_token
        return headers

    def get(self, uri, co3_context_token=None):
        """Gets the specified URI.  Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So
        for example, if you specify a uri of /incidents, the actual URL would be something like this:
   
            https://app.co3sys.com/rest/orgs/201/incidents
   
        Args:
          uri
          co3_context_token
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          SimpleHTTPException - if an HTTP exception occurrs.
        """
   
        url = "{}/rest/orgs/{}{}".format(self.base_url, self.org_id, uri)

        response = self.session.get(url, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        self._raise_if_error(response)

        return json.loads(response.text)

    def post(self, uri, payload, co3_context_token = None):
        """
        Posts to the specified URI.
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you 
        specify a uri of /incidents, the actual URL would be something like this:
   
            https://app.co3sys.com/rest/orgs/201/incidents
        Args:
           uri
           payload
           co3_context_token
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          SimpleHTTPException - if an HTTP exception occurrs.
        """

        url = "{}/rest/orgs/{}{}".format(self.base_url, self.org_id, uri)

        payload_json = json.dumps(payload)

        response = self.session.post(url, data=payload_json, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        self._raise_if_error(response)

        return json.loads(response.text)
   
    def _get_put(self, uri, apply_func, co3_context_token):
        """Internal helper to do a get/apply/put loop (for situations where the put might return a 409/conflict status code"""
        url = "{}/rest/orgs/{}{}".format(self.base_url, self.org_id, uri)

        response = self.session.get(url, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        self._raise_if_error(response)

        payload = json.loads(response.text)

        apply_func(payload)

        payload_json = json.dumps(payload)

        response = self.session.put(url, data=payload_json, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        if response.status_code == 200:
            return json.loads(response.text)
        elif response.status_code == 409:
            return None

        self._raise_if_error(response)

        return None

    def get_put(self, uri, apply_func, co3_context_token = None):
        """Performs a get, calls apply_func on the returned value, then calls self.put.
        If the put call returns a 409 error, then retry.

        Args:
          uri - the URI to use.  Note that this is expected to be relative to the org.
          apply_func - a function to call on the object returned by get.  This is expected
          to alter the object with the desired changes.
          co3_context_token - the Co3ContextToken from a CAF message (if the caller is
          a CAF message processor.
        Returns;
          The object returned by the put operation (converted from JSON to a Python dict).
        Raises:
          Exception if the get or put returns an unexpected status code.
        """
        while True:
            obj = self._get_put(uri, apply_func, co3_context_token)

            if obj:
                return obj

        return None

    def put(self, uri, payload, co3_context_token = None):
        """
        Puts to the specified URI.
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you 
        specify a uri of /incidents, the actual URL would be something like this:
   
            https://app.co3sys.com/rest/orgs/201/incidents
        Args:
           uri
           payload
           co3_context_token
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          SimpleHTTPException - if an HTTP exception occurrs.
        """        
        url = "{}/rest/orgs/{}{}".format(self.base_url, self.org_id, uri)

        payload_json = json.dumps(payload)

        response = self.session.put(url, data=payload_json, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        self._raise_if_error(response)

        return json.loads(response.text)

    def delete(self, uri, co3_context_token = None):
        """Deletes the specified URI.

        Args:
          uri
          co3_context_token
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you 
        specify a uri of /incidents, the actual URL would be something like this:
   
            https://app.co3sys.com/rest/orgs/201/incidents
        Args:
           uri
           co3_context_token
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          SimpleHTTPException - if an HTTP exception occurrs.
        """

        url = "{}/rest/orgs/{}{}".format(self.base_url, self.org_id, uri)

        response = self.session.delete(url, cookies=self.cookies, headers=self.__make_headers(co3_context_token), verify=self.verify)

        if (response.status_code == 204):
            # 204 - No content is OK for a delete
            return None

        self._raise_if_error(response)

        return json.loads(response.text)

    def _raise_if_error(self, response):
        """Helper to raise a SimpleHTTPException if the response.status_code is not 200.

        Args:
          response - the Response object from a get/put/etc.
        Raises:
          SimpleHTTPException - if response.status_code is not 200.
        """
        if response.status_code != 200:
            raise SimpleHTTPException(response)

