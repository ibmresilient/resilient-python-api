#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import logging
import os
from resilient import parse_parameters, get_config_file
import resilient_circuits.keyring_arguments as keyring_arguments
from resilient_circuits.validate_configs import VALIDATE_DICT
from resilient_circuits.helpers import validate_configs
from resilient_circuits import constants


class AppArgumentParser(keyring_arguments.ArgumentParser):
    """Helper to parse command line arguments."""
    DEFAULT_APP_SECTION = "resilient"
    DEFAULT_STOMP_PORT = 65001
    DEFAULT_COMPONENTS_DIR = ''
    DEFAULT_LOG_LEVEL = 'INFO'
    DEFAULT_LOG_FILE = 'app.log'
    DEFAULT_NO_PROMPT_PASS = "False"
    DEFAULT_STOMP_TIMEOUT = 60
    DEFAULT_STOMP_MAX_RETRIES = 3
    DEFAULT_MAX_CONNECTION_RETRIES = 1
    DEFAULT_NUM_WORKERS = 10

    def __init__(self, config_file=None):

        # Temporary logging handler until the real one is created later
        temp_handler = logging.StreamHandler()
        temp_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(module)s] %(message)s'))
        temp_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(temp_handler)
        config_file = config_file or get_config_file()
        super(AppArgumentParser, self).__init__(config_file=config_file)

        default_components_dir = self.getopt(self.DEFAULT_APP_SECTION, "componentsdir") or self.DEFAULT_COMPONENTS_DIR
        default_noload = self.getopt(self.DEFAULT_APP_SECTION, "noload") or ""
        default_log_dir = self.getopt(self.DEFAULT_APP_SECTION, "logdir") or constants.APP_LOG_DIR
        default_log_level = self.getopt(self.DEFAULT_APP_SECTION, "loglevel") or self.DEFAULT_LOG_LEVEL
        default_log_file = self.getopt(self.DEFAULT_APP_SECTION, "logfile") or self.DEFAULT_LOG_FILE

        # STOMP port is usually 65001
        default_stomp_port = self.getopt(self.DEFAULT_APP_SECTION, "stomp_port") or self.DEFAULT_STOMP_PORT
        # For some environments the STOMP TLS certificate will be different from the REST API cert
        default_stomp_cafile = self.getopt(self.DEFAULT_APP_SECTION, "stomp_cafile") or None

        default_stomp_url = self.getopt(self.DEFAULT_APP_SECTION, "stomp_host") or self.getopt(self.DEFAULT_APP_SECTION, "host")
        default_stomp_timeout = self.getopt(self.DEFAULT_APP_SECTION, "stomp_timeout") or self.DEFAULT_STOMP_TIMEOUT
        default_stomp_max_retries = self.getopt(self.DEFAULT_APP_SECTION, "stomp_max_retries") or self.DEFAULT_STOMP_MAX_RETRIES
        default_max_connection_retries = self.getopt(self.DEFAULT_APP_SECTION, "max_connection_retries") or self.DEFAULT_MAX_CONNECTION_RETRIES

        default_no_prompt_password = self.getopt(self.DEFAULT_APP_SECTION,
                                                 "no_prompt_password") or self.DEFAULT_NO_PROMPT_PASS
        default_no_prompt_password = self._is_true(default_no_prompt_password)

        default_test_actions = self._is_true(self.getopt(self.DEFAULT_APP_SECTION,
                                                         "test_actions")) or False
        default_test_host = self.getopt(self.DEFAULT_APP_SECTION, "test_host") or None
        default_test_port = self.getopt(self.DEFAULT_APP_SECTION, "test_port") or None
        default_log_responses = self.getopt(self.DEFAULT_APP_SECTION,
                                            "log_http_responses") or ""
        default_resource_prefix = self.getopt(self.DEFAULT_APP_SECTION, "resource_prefix") or None
        default_num_workers = self.getopt(self.DEFAULT_APP_SECTION, "num_workers") or self.DEFAULT_NUM_WORKERS

        logging.getLogger().removeHandler(temp_handler)

        self.add_argument("--stomp-host",
                          type=str,
                          default=default_stomp_url,
                          help="Resilient server STOMP host url")
        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")
        self.add_argument("--stomp-cafile",
                          type=str,
                          action="store",
                          default=default_stomp_cafile,
                          help="Resilient server STOMP TLS certificate")
        self.add_argument("--stomp-timeout",
                          type=int,
                          action="store",
                          default=os.environ.get('RESILIENT_STOMP_TIMEOUT', default_stomp_timeout),
                          help="Resilient server STOMP timeout for connections")
        self.add_argument("--stomp-max-retries",
                          type=int,
                          action="store",
                          default=os.environ.get('RESILIENT_STOMP_MAX_RETRIES', default_stomp_max_retries),
                          help="Resilient server STOMP max retries before failing")
        self.add_argument("--max-connection-retries",
                          type=int,
                          action="store",
                          default=os.environ.get('RESILIENT_MAX_CONNECTION_RETRIES') or 0 if os.environ.get("APP_HOST_CONTAINER") else default_max_connection_retries,
                          help="Resilient max retries when connecting to Resilient or 0 for unlimited")
        self.add_argument("--resource-prefix",
                          type=str,
                          action="store",
                          default=os.environ.get('RESOURCE_PREFIX', default_resource_prefix),
                          help="Cloud Pak for Security resource path for host and STOMP URLs")
        self.add_argument("--componentsdir",
                          type=str,
                          default=default_components_dir,
                          help="Circuits components auto-load directory")
        self.add_argument("--noload",
                          type=str,
                          default=default_noload,
                          help="List of components that should not be loaded")
        self.add_argument("--logdir",
                          type=str,
                          default=default_log_dir,
                          help="Directory for log files")
        self.add_argument("--loglevel",
                          type=str,
                          default=default_log_level,
                          help="Log level")
        self.add_argument("--logfile",
                          type=str,
                          default=default_log_file,
                          help="File to log to")
        self.add_argument("--no-prompt-password",
                          type=bool,
                          default=default_no_prompt_password,
                          help="Never prompt for password on stdin")
        self.add_argument("--test-actions",
                          action="store_true",
                          default=default_test_actions,
                          help="Enable submitting test actions?")
        self.add_argument("--test-host",
                          type=str,
                          action="store",
                          default=default_test_host,
                          help=("For use with --test-actions option. "
                                "Host or IP to bind test server to."))
        self.add_argument("--test-port",
                          type=int,
                          action="store",
                          default=default_test_port,
                          help=("For use with --test-actions option. "
                                "Port to bind test server to."))
        self.add_argument("--log-http-responses",
                          type=str,
                          default=default_log_responses,
                          help=("Log all responses from Resilient "
                                "REST API to this directory"))
        self.add_argument("--num-workers",
                          type=int,
                          default=default_num_workers,
                          help=("Number of FunctionWorkers to use. "
                                "Number of Functions that can run in parallel"))

    def parse_args(self, args=None, namespace=None, ALLOW_UNRECOGNIZED=False):
        """Parse commandline arguments and construct an opts dictionary"""
        opts = super(AppArgumentParser, self).parse_args(args, namespace, ALLOW_UNRECOGNIZED)
        if self.config:
            for section in self.config.sections():
                items = dict((item.lower(), self.config.get(section, item)) for item in self.config.options(section))
                opts.update({section: items})

            parse_parameters(opts)

        validate_configs(opts, VALIDATE_DICT)

        return opts

    @staticmethod
    def _is_true(value):
        if value:
            return value.lower()[0] in ("1", "t", "y")
        else:
            return False
