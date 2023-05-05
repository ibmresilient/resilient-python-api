#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging
import os

from resilient import constants as res_constants
from resilient import get_config_file
from resilient import helpers as res_helpers
from resilient import parse_parameters

import resilient_circuits.keyring_arguments as keyring_arguments
from resilient_circuits import constants
from resilient_circuits.helpers import validate_configs
from resilient_circuits.validate_configs import VALIDATE_DICT


class AppArgumentParser(keyring_arguments.ArgumentParser):
    """Helper to parse command line arguments."""
    DEFAULT_APP_SECTION = "resilient"
    DEFAULT_STOMP_PORT = 65001
    DEFAULT_COMPONENTS_DIR = ''
    DEFAULT_LOG_LEVEL = 'INFO'
    DEFAULT_LOG_FILE = 'app.log'
    DEFAULT_LOG_MAX_BYTES = 10000000
    DEFAULT_LOG_BACKUP_COUNT = 10
    DEFAULT_NO_PROMPT_PASS = "False"
    DEFAULT_STOMP_TIMEOUT = 60
    DEFAULT_STOMP_MAX_RETRIES = 3
    DEFAULT_MAX_CONNECTION_RETRIES = res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES_DEFAULT
    DEFAULT_NUM_WORKERS = 25
    DEFAULT_APP_EXCEPTION = False
    DEFAULT_HEARTBEAT_TIMEOUT_THRESHOLD = None
    DEFAULT_RC_USE_PERSISTENT_SESSIONS = True

    def __init__(self, config_file=None):

        self._setup_temp_logger()
        config_file = config_file or get_config_file()
        super(AppArgumentParser, self).__init__(config_file=config_file)

        default_components_dir = self.getopt(self.DEFAULT_APP_SECTION, "componentsdir") or self.DEFAULT_COMPONENTS_DIR
        default_noload = self.getopt(self.DEFAULT_APP_SECTION, "noload") or ""
        default_log_dir = self.getopt(self.DEFAULT_APP_SECTION, "logdir") or constants.APP_LOG_DIR
        default_log_level = self.getopt(self.DEFAULT_APP_SECTION, "loglevel") or self.DEFAULT_LOG_LEVEL
        default_log_file = self.getopt(self.DEFAULT_APP_SECTION, "logfile") or self.DEFAULT_LOG_FILE
        default_log_max_bytes = self.getopt(self.DEFAULT_APP_SECTION, constants.APP_CONFIG_LOG_MAX_BYTES) or self.DEFAULT_LOG_MAX_BYTES
        default_log_backup_count = self.getopt(self.DEFAULT_APP_SECTION, constants.APP_CONFIG_LOG_BACKUP_COUNT) or self.DEFAULT_LOG_BACKUP_COUNT

        # STOMP port is usually 65001
        default_stomp_port = self.getopt(self.DEFAULT_APP_SECTION, "stomp_port") or self.DEFAULT_STOMP_PORT
        # For some environments the STOMP TLS certificate will be different from the REST API cert
        default_stomp_cafile = self.getopt(self.DEFAULT_APP_SECTION, "stomp_cafile") or None

        default_stomp_url = self.getopt(self.DEFAULT_APP_SECTION, "stomp_host") or self.getopt(self.DEFAULT_APP_SECTION, "host")
        default_stomp_timeout = self.getopt(self.DEFAULT_APP_SECTION, "stomp_timeout") or self.DEFAULT_STOMP_TIMEOUT
        default_stomp_max_retries = self.getopt(self.DEFAULT_APP_SECTION, "stomp_max_retries") or self.DEFAULT_STOMP_MAX_RETRIES
        default_max_connection_retries = self.getopt(self.DEFAULT_APP_SECTION, res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES) or self.DEFAULT_MAX_CONNECTION_RETRIES

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
        default_trap_exception = self.getopt(self.DEFAULT_APP_SECTION, constants.APP_CONFIG_TRAP_EXCEPTION) or self.DEFAULT_APP_EXCEPTION
        default_trap_exception = self._is_true(default_trap_exception)

        default_heartbeat_timeout_threshold = self.getopt(self.DEFAULT_APP_SECTION, constants.APP_CONFIG_HEARTBEAT_TIMEOUT_THRESHOLD) or self.DEFAULT_HEARTBEAT_TIMEOUT_THRESHOLD
        default_rc_use_persistent_sessions = self.getopt(self.DEFAULT_APP_SECTION, constants.APP_CONFIG_RC_USE_PERSISTENT_SESSIONS) or self.DEFAULT_RC_USE_PERSISTENT_SESSIONS

        self._unset_temp_logger()

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
                          help="Number of attempts to retry when connecting to SOAR. Use 0 or -1 for unlimited retries. Defaults to 0")
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
        self.add_argument("--{0}".format(constants.APP_CONFIG_LOG_MAX_BYTES),
                          type=int,
                          default=default_log_max_bytes,
                          help="Maximum bytes per log file")
        self.add_argument("--{0}".format(constants.APP_CONFIG_LOG_BACKUP_COUNT),
                          type=int,
                          default=default_log_backup_count,
                          help="Number of log files to create in rotation")
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
        self.add_argument("--trap-exception",
                          type=bool,
                          default=default_trap_exception,
                          help=("If set to 'True' a Function's exception will be ignored"))
        self.add_argument("--{0}".format(constants.APP_CONFIG_HEARTBEAT_TIMEOUT_THRESHOLD),
                          type=int,
                          default=default_heartbeat_timeout_threshold,
                          help=("The amount of time in seconds that can occur between HeartbeatTimeouts before exiting"))
        self.add_argument("--{0}".format(constants.APP_CONFIG_RC_USE_PERSISTENT_SESSIONS),
                          type=str,
                          default=default_rc_use_persistent_sessions,
                          help=("Set to False to disable the use of persistent sessions with RequestsCommon in app functions"))

    def parse_args(self, args=None, namespace=None, ALLOW_UNRECOGNIZED=False):
        """Parse commandline arguments and construct an opts dictionary"""
        self._setup_temp_logger()
        opts = super(AppArgumentParser, self).parse_args(args, namespace, ALLOW_UNRECOGNIZED)
        if self.config:
            for section in self.config.sections():
                items = dict((item.lower(), self.config.get(section, item)) for item in self.config.options(section))
                opts.update({section: items})

            opts = parse_parameters(opts)

            # Once we have read the app.config and decrypted any protected secrets
            # we must remove the secrets directory
            res_helpers.remove_secrets_dir()

        validate_configs(opts, VALIDATE_DICT)

        # NOTE: Newer retry2 logic requires tries to be -1 (not 0 as before) for unlimited attempts
        if opts.get(res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES, -1) == 0:
            opts[res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES] = -1

        self._unset_temp_logger()
        return opts

    def _setup_temp_logger(self):
        # Temporary logging handler until the real one is created later in app.py
        # return
        self.temp_handler = logging.StreamHandler()
        self.temp_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(module)s] %(message)s'))
        self.temp_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(self.temp_handler)

    def _unset_temp_logger(self):
        # Unset the temporary logger
        # return
        logging.getLogger().removeHandler(self.temp_handler)

    @staticmethod
    def _is_true(value):
        if value:
            return value.lower()[0] in ("1", "t", "y")
        else:
            return False
