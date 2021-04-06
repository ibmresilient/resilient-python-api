#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Implementation of AppFunctionComponent"""

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
        self.app_configs = validate_fields(required_app_configs, opts.get(package_name, {}))
        self.rc = RequestsCommon(opts=opts, function_opts=self.app_configs)

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
