# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import requests
from .integration_errors import IntegrationError


def execute_call(verb, url, payload, log=None, basicauth=None, verify_flag=True, headers=None,
                 proxies=None, timeout=None, resp_type='json', callback=None):
    """
    Function: perform the http API call. Different types of http operations are supported:
    GET, POST, PUT
    Errors raise IntegrationError
    If a callback method is provided, then it's called to handle the error

    :param verb: GET, POST, PUT, DELETE
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

        if verb == 'get':
            resp = requests.get(url, verify=verify_flag, headers=headers, params=payload,
                                auth=basicauth, timeout=timeout, proxies=proxies)
        elif verb == 'post':
            resp = requests.post(url, verify=verify_flag, headers=headers, data=payload,
                                 auth=basicauth, timeout=timeout, proxies=proxies)
        elif verb == 'put':
            resp = requests.put(url, verify=verify_flag, headers=headers, data=payload,
                                auth=basicauth, timeout=timeout, proxies=proxies)
        elif verb == 'patch':
            resp = requests.patch(url, verify=verify_flag, headers=headers, data=payload,
                                  auth=basicauth, timeout=timeout, proxies=proxies)
        elif verb == 'delete':
            resp = requests.delete(url, verify=verify_flag, headers=headers, data=payload,
                                   auth=basicauth, timeout=timeout, proxies=proxies)
        else:
            raise IntegrationError("unknown verb {}".format(verb))

        if resp is None:
            raise IntegrationError('no response returned')

        # custom handler for response handling?
        if callback:
            return callback(resp)

        # standard error handling
        if resp.status_code >= 300:
            # get the result
            raise IntegrationError(resp.text)

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
        log and log.error(err)
        raise IntegrationError(err)
