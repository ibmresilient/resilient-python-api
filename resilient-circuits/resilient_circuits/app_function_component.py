#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Implementation of AppFunctionComponent"""

import logging
import threading
from collections import namedtuple
from resilient_circuits import ResilientComponent, handler, StatusMessage
from resilient_lib import RequestsCommon, validate_fields


class AppFunctionComponent(ResilientComponent):

    def __init__(self, opts, package_name, required_app_configs=[]):
        """
        Set the PACKAGE_NAME and required_app_configs, validate the app_configs
        If a required_app_config is not found in opts, raise a ValueError
        Instansiate a new resilient_lib.RequestsCommon object 'rc'
        """

        self.PACKAGE_NAME = package_name

        self._required_app_configs = required_app_configs

        # Validate app_configs and get dictionary as result
        self._app_configs_as_dict = validate_fields(required_app_configs, opts.get(package_name, {}))

        # This variable also is used to get the app.configs
        self.options = self._app_configs_as_dict

        # Instansiate RequestsCommon with dictionary of _app_configs_as_dict
        self.rc = RequestsCommon(opts=opts, function_opts=self._app_configs_as_dict)

        # Convert _app_configs_as_dict to namedtuple
        self.app_configs = namedtuple("app_configs", self._app_configs_as_dict.keys())(*self._app_configs_as_dict.values())

        self._local_storage = threading.local()

        self.LOG = logging.getLogger(__name__)

        super(AppFunctionComponent, self).__init__(opts)

    @property
    def required_app_configs(self):
        return self._required_app_configs

    @required_app_configs.setter
    def required_app_configs(self, value):
        self._required_app_configs = value

    @handler("reload")
    def _reload(self, event, opts):
        self.app_configs = validate_fields(self.required_app_configs, opts.get(self.PACKAGE_NAME, {}))

    @staticmethod
    def status_message(message):
        """
        Returns the message encapsulated in a
        resilient_circuits.StatusMessage object

        :param message: Message you want to sent to Action Status
        :type message: str

        :return: message encapsulated as StatusMessage
        :rtype: resilient_circuits.StatusMessage
        """
        return StatusMessage(message)

    def set_fn_msg(self, message_dict):
        """
        Uses threading.local() to store the message received
        locally for this Thread. Is accessed using the
        `get_fn_msg()` method below

        :param message_dict: Message received from SOAR
        :type message: dict
        """
        self._local_storage.fn_msg = message_dict

    def get_fn_msg(self):
        """
        If 'fn_msg' is defined in local Thread storage,
        return it, else return an empty dictionary

        :return: Message received from SOAR
        :rtype: dict
        """
        fn_msg = {}

        try:
            fn_msg = self._local_storage.fn_msg
        except AttributeError as err:
            self.LOG.warning("fn_msg could not be found\n%s", err)

        return fn_msg
