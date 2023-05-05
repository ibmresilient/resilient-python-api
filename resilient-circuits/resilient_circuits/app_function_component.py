#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Implementation of AppFunctionComponent"""

import logging
import threading
from collections import namedtuple

from resilient_circuits import (ResilientComponent, StatusMessage, constants,
                                handler)
from resilient_circuits.app_argument_parser import AppArgumentParser
from resilient_lib import (RequestsCommon, RequestsCommonWithoutSession,
                           str_to_bool, validate_fields)


class AppFunctionComponent(ResilientComponent):
    """
    Each package that has been generated with the ``resilient-sdk codegen`` command
    that contains a SOAR Function, an :class:`AppFunctionComponent` will be generated
    in the package's ``components`` directory

    Each :class:`AppFunctionComponent`, gets loaded into the ``resilient-circuits`` framework
    and listens for messages on it's ``Message Destination``
    """

    def __init__(self, opts, package_name, required_app_configs=[]):
        """
        Sets and exposes 4 properties:
            #. **self.PACKAGE_NAME**: the name of this App, the parameter passed in
            #. **self.app_configs**: a `collections.namedtuple <https://docs.python.org/3.6/library/collections.html#collections.namedtuple>`_
               object of all associated configurations in the ``app.config`` file for this. App Configurations can be accessed like:

               .. code-block:: python

                     base_url = self.app_configs.base_url

            #. **self.rc**: an instantiation of :class:`resilient_lib.RequestsCommon <resilient_lib.components.requests_common.RequestsCommon>`
               which will have access to the ``execute`` method for external API calls
            #. **self.LOG**: access to a common ``Logger`` object. Can be used like:

               .. code-block:: python

                     self.LOG.info("Starting '%s'", self.PACKAGE_NAME)

        :param opts: all configurations from the ``app.config`` file
        :type opts: dict
        :param package_name: the name of this App
        :type package_name: str
        :param required_app_configs: a list of required ``app.config`` configurations
            that are required to run this App
        :type required_app_configs: [str, str, ...]
        :raises ValueError: if a ``required_app_config`` is not found in ``opts``
        """

        self.PACKAGE_NAME = package_name

        self._required_app_configs = required_app_configs

        # Validate app_configs and get dictionary as result
        self._app_configs_as_dict = validate_fields(required_app_configs, opts.get(package_name, {}))

        # This variable also is used to get the app.configs
        self.options = self._app_configs_as_dict

        # Instantiate RequestsCommon with dictionary of _app_configs_as_dict
        if str_to_bool(opts.get(constants.APP_CONFIG_RC_USE_PERSISTENT_SESSIONS, AppArgumentParser.DEFAULT_RC_USE_PERSISTENT_SESSIONS)):
            requests_common_type = RequestsCommon
        else:
            requests_common_type = RequestsCommonWithoutSession

        self.rc = requests_common_type(opts=opts, function_opts=self._app_configs_as_dict)

        # NOTE: self.app_configs used to be a namedtuple.
        # Since v49 this is no longer a namedtuple.
        # It behaves the same way that a namedtuple would, but
        # instead is a resilient.app_config.AppConfig object.
        # This allows for pluggable PAM connectors/plugins
        self.app_configs = self._app_configs_as_dict

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
        ``resilient_circuits.StatusMessage`` object

        **Usage:**

        .. code-block:: python

            yield self.status_message("Finished running App Function: '{0}'".format(FN_NAME))

        :param message: Message you want to send to Action Status
        :type message: str

        :return: message encapsulated as ``StatusMessage``
        :rtype: ``resilient_circuits.StatusMessage``
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
        Get the STOMP Message that has been sent from
        SOAR as a dict. The contents of the Message
        can include:

        .. code-block:: python

            'function': {
                'creator': '',
                'description': '',
                'display_name': 'mock_function',
                'id': 3,
                'name': 'mock_function',
                'tags': [...],
                'uuid': '',
                'version': None,
                'view_items': [...],
                ...
            },
            'groups': [],
            'inputs': {
                'mock_input_one': True,
                'mock_input_two': 'abc',
            },
            'playbook_instance': None,
            'principal': {
                'display_name': '',
                'id': 1,
                'name': '',
                'type': 'user'
            },
            'workflow': {
                'actions': [...],
                'description': '',
                'name': '',
                'object_type': { ... },
                'programmatic_name': '',
                'tags': [...],
                'uuid': '',
                'workflow_id': 3
            },
            'workflow_instance': {
                'workflow_instance_id': 54
            }

        :return: STOMP Message received from SOAR
        :rtype: dict
        """
        fn_msg = {}

        try:
            fn_msg = self._local_storage.fn_msg
        except AttributeError as err:
            self.LOG.warning("fn_msg could not be found\n%s", err)

        return fn_msg
