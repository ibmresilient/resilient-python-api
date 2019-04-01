# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2019. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import requests
from resilient_lib.components.integration_errors import IntegrationError


class RequestsCommon:
    """
    This class represents common functions around the use of the requests package for REST based APIs.
    It incorporates the app.config section "integrations" which can be used to define a common set of proxies
    for use by all functions using this library:

    [integrations]
    http_proxy=
    https_proxy=

    Similar properties may exist in the function's section which would override the [integrations] properties.
    """
    def __init__(self, opts=None, function_opts=None):
        # capture the properties for the integration as well as the global settings for all integrations for proxy urls
        self.integration_options = opts.get('integrations', None) if opts else None
        self.function_opts = function_opts

    def get_proxies(self):
        """ proxies can be specified globally for all integrations or specifically per function """
        proxies = None
        if self.integration_options and (self.integration_options.get("http_proxy") or self.integration_options.get("https_proxy")):
            proxies = {'http': self.integration_options.get("http_proxy"), 'https': self.integration_options.get("https_proxy")}

        if self.function_opts and (self.function_opts.get("http_proxy") or self.function_opts.get("https_proxy")):
            proxies = {'http': self.function_opts.get("http_proxy"), 'https': self.function_opts.get("https_proxy")}

        return proxies

    def execute_call(self, verb, url, payload={}, log=None, basicauth=None, verify_flag=True, headers=None,
                     proxies=None, timeout=None, resp_type='json', callback=None):
        """
        Function: perform the http API call. Different types of http operations are supported:
        GET, HEAD, PATCH, POST, PUT, DELETE
        Errors raise IntegrationError
        If a callback method is provided, then it's called to handle the error

        When using argument 'json' Content-Type will automatically be set to "application/json" by requests lib.

        :param verb: GET, HEAD, PATCH, POST, PUT, DELETE
        :param url:
        :param basicauth: used for basic authentication - (user, password)
        :param payload:
        :param log: optional log statement
        :param verify_flag: True/False - False used for debugging generally
        :param headers: dictionary of http headers
        :param proxies: http and https proxies for call
        :param timeout: timeout before call should abort
        :param resp_type: type of output to return: json, text, bytes
        :param callback: callback routine used to handle errors
        :return: json of returned data
        """

        try:
            (payload and log) and log.debug(payload)

            if verb.lower() not in ('get', 'post', 'put', 'patch', 'delete', 'head'):
                raise IntegrationError("unknown verb {}".format(verb))

            if proxies is None:
                proxies = self.get_proxies()

            if verb.lower() == 'post':

                content_type = get_case_insensitive_key_value(headers, "Content-Type")

                if is_payload_in_json(content_type):
                    resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, json=payload,
                                            auth=basicauth, timeout=timeout, proxies=proxies)
                else:
                    resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, data=payload,
                                            auth=basicauth, timeout=timeout, proxies=proxies)
            else:
                resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, params=payload,
                                        auth=basicauth, timeout=timeout, proxies=proxies)

            if resp is None:
                raise IntegrationError('no response returned')

            # custom handler for response handling?
            if callback:
                return callback(resp)

            # standard error handling
            if resp.status_code >= 300:
                # get the result
                # log resp.status_code in case resp.text isn't available
                raise IntegrationError(
                    "status_code: {}, msg: {}".format(resp.status_code, resp.text if resp.text else "N/A"))

            # check if anything returned
            log and log.debug(resp.text)

            # get the result
            if resp_type == 'json':
                r = resp.json()
            elif resp_type == 'text':
                r = resp.text
            elif resp_type == 'bytes':
                r = resp.content
            else:
                raise IntegrationError("incorrect response type: {}".format(resp_type))

            # Produce a IntegrationError with the return value
            return r      # json object needed, not a string representation
        except Exception as err:
            msg = str(err)
            log and log.error(msg)
            raise IntegrationError(msg)


def is_payload_in_json(content_type):
    """
    Verify the content_type.
    If "Content-Type" is NOT specified pass the payload to the "json" argument - return True.

    If "Content-Type" is specified:
        - if the value is "application/json" pass the payload to the "json" argument - return True.
        - if the value is NOT "application/json" pass the payload to the "data" argument - return False.
    :param content_type:
    :return: True or False
    """

    if not content_type:
        return True

    return "application/json" in content_type.lower()


def get_case_insensitive_key_value(dictionary, key):
    """
    Get case insensitive key value from dictionary.
    :param dictionary:
    :param key:
    :return: value or None
    """
    if dictionary is None:
        return None

    return next((v for k, v in dictionary.items() if k.lower() == key.lower()), None)
