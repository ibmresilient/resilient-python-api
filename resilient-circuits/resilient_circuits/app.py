#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Action Module server

This uses the `Circuits <http://circuitsframework.com/>` framework to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

"""

from __future__ import print_function

import logging
from logging.handlers import RotatingFileHandler
import os
import filelock
from circuits import Manager, BaseComponent, Component, Debugger, Loader
import resilient
from resilient import parse_parameters
from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits.actions_component import Actions, ResilientComponent
import resilient_circuits.keyring_arguments as keyring_arguments
from resilient_circuits.validate_configs import VALIDATE_DICT
from resilient_circuits.helpers import validate_configs
from six import string_types
import re

APP_LOG_DIR = os.environ.get("APP_LOG_DIR", "logs")
PASSWD_PATTERNS = ['passcode','password','passwd','secret','pin']

application = None
logging_initialized = False

class RedactingFilter(logging.Filter):
    """ Redacting logging filter to prevent Resilient circuits sensitive password values from being logged.

    """
    def __init__(self):
        super(RedactingFilter, self).__init__()

    def filter(self, record):
        # Best effort regex filter pattern to redact password logging.
        if isinstance(record.msg, string_types):
            for p in PASSWD_PATTERNS:
                if p in record.msg.lower():
                    record.msg = re.sub(r"(?i)^(.*)({})(.*?:\s*)(.+?)((?:[\s,].*)*)$".format(p),
                                        r"\1\2\3***\5", record.msg)
        return True


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
        config_file = config_file or resilient.get_config_file()
        super(AppArgumentParser, self).__init__(config_file=config_file)

        default_components_dir = self.getopt(self.DEFAULT_APP_SECTION, "componentsdir") or self.DEFAULT_COMPONENTS_DIR
        default_noload = self.getopt(self.DEFAULT_APP_SECTION, "noload") or ""
        default_log_dir = self.getopt(self.DEFAULT_APP_SECTION, "logdir") or APP_LOG_DIR
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

    def parse_args(self, args=None, namespace=None):
        """Parse commandline arguments and construct an opts dictionary"""
        opts = super(AppArgumentParser, self).parse_args(args, namespace)
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


# Main component for our application
class App(Component):
    """Our main app component, which sets up the Resilient services and other components"""

    FILE_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
    SYSLOG_LOG_FORMAT = '%(module)s: %(levelname)s %(message)s'
    STDERR_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

    def __init__(self, auto_load_components=True, config_file=None):
        super(App, self).__init__()
        # Read the configuration options
        self.action_component = None
        self.component_loader = None
        self.auto_load_components = auto_load_components
        self.config_file = config_file or resilient.get_config_file()
        self.do_initialization()

    def do_initialization(self):
        self.opts = AppArgumentParser(config_file=self.config_file).parse_args()

        self.config_logging(self.opts["logdir"], self.opts["loglevel"], self.opts['logfile'])
        LOG.info("Configuration file: %s", self.config_file)
        LOG.info("Resilient server: %s", self.opts.get("host"))
        if self.opts.get("email", None):
            LOG.info("Resilient user: %s", self.opts.get("email"))
        if self.opts.get("api_key_id", None):
            LOG.info("Resilient api key id: %s", self.opts.get("api_key_id"))
        if self.opts.get("api_key_id", None) and self.opts.get("email", None):
            LOG.warning("The user and api key configuration settings are both enabled. Credentials will default to the "
                        "api key settings.")
        LOG.info("Resilient org: %s", self.opts.get("org"))
        LOG.info("Logging Level: %s", self.opts.get("loglevel"))
        if self.opts.get("test_actions", False):
            # Make all components aware that we are in test mode
            ResilientComponent.test_mode = True

        # Connect to events from Action Module.
        # Note: this must be done before components are loaded, because it uses
        # each component's "channel" to initiate subscription to the message queue.
        if self.opts.get("resilient", None) and self.opts["resilient"].get("actions_component", None):
            # user specified actions_component to use
            path, filename = os.path.split(self.opts["resilient"]["actions_component"])
            LOG.info("User specified actions_component: {}, from {}".format(filename, path))
            loader = Loader(init_kwargs={"opts": self.opts},
                            paths=[path])
            self.action_component = loader.load(filename)
        else:
            self.action_component = Actions(self.opts)
        self.action_component.register(self)

        # Register a `loader` to dynamically load
        # all Circuits components in the 'componentsdir' directory
        if self.auto_load_components:
            LOG.info("Components auto-load directory: %s",
                     self.opts["componentsdir"] or "(none)")
            if not self.component_loader:
                self.component_loader = ComponentLoader(self.opts)
            else:
                LOG.info("Updating and re-registering ComponentLoader")
                self.component_loader.opts = self.opts
            self.component_loader.register(self)

    def config_logging(self, logdir, loglevel, logfile):
        """ set up some logging """
        global LOG_PATH, LOG, logging_initialized

        LOG_PATH = os.path.join(logdir, logfile)
        LOG_PATH = os.path.expanduser(LOG_PATH)
        LOG = logging.getLogger(__name__)

        # Only do this once! (mostly for pytest)
        if logging_initialized:
            LOG.info("Logging already initialized.")
            return
        logging_initialized = True

        # Ignore syslog errors from message-too-long
        logging.raiseExceptions = False

        try:
            numeric_level = getattr(logging, loglevel)
            logging.getLogger().setLevel(numeric_level)
        except AttributeError as e:
            logging.getLogger().setLevel(logging.INFO)
            LOG.warning("Invalid logging level specified. Using INFO level")

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self += Debugger()

        file_handler = RotatingFileHandler(LOG_PATH, maxBytes=10000000,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(self.FILE_LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)
        syslog = logging.handlers.SysLogHandler()
        syslog.setFormatter(logging.Formatter(self.SYSLOG_LOG_FORMAT))
        logging.getLogger().addHandler(syslog)
        stderr = logging.StreamHandler()
        stderr.setFormatter(logging.Formatter(self.STDERR_LOG_FORMAT))
        logging.getLogger().addHandler(stderr)
        # Add password redacting filter for logging.
        syslog.addFilter(RedactingFilter())
        file_handler.addFilter(RedactingFilter())
        stderr.addFilter(RedactingFilter())

    def load_all_success(self, event):
        """OK, component loader says we're ready"""
        LOG.info("Components loaded")

        # For debugging, print out the tree of all loaded components
        def walk(depth, component):
            yield (u"  " * depth) + repr(component)
            if isinstance(component, BaseComponent) and callable(component.events):
                for event in component.events():
                    channels = ", ".join([h.channel or '*' for h in list(component._handlers[event])])
                    yield u"{}{}/{}".format((u"  " * (depth+1)), event, channels)
            if isinstance(component, Manager):
                for c in component.components:
                    for thing in walk(depth+1, c):
                        yield thing
        tree = walk(1, self.root)
        LOG.debug(u"Components:\n" + ("\n".join(tree)))

    def load_all_failure(self, event):
        """OK, component loader says we're unable to start"""
        LOG.error("A component failed to load.  The application cannot start.")
        self.stop()

    def reload_opts(self):
        """Reload the configuration options in case they changed"""
        LOG.debug("Reload opts")
        self.opts.update(AppArgumentParser().parse_args())

    def started(self, event, component):
        """Started Event Handler"""
        LOG.info("App Started")

    def stopped(self, event, component):
        """Stopped Event Handler"""
        LOG.info("App Stopped")


def get_lock():
    """Create a filelock"""

    # The run() method uses a file lock in the user's ~/.resilient directory to prevent multiple instances
    # of resilient circuits running.  You can override the lockfile name in the
    # (and so allow multiple) by setting APP_LOCK_FILE in the environment.
    app_lock_file = os.environ.get("APP_LOCK_FILE", "")

    if not app_lock_file:
        lockfile = os.path.expanduser(os.path.join("~", ".resilient", "resilient_circuits_lockfile"))
        resilient_dir = os.path.dirname(lockfile)
        if not os.path.exists(resilient_dir):
            os.makedirs(resilient_dir)
    else:
        lockfile = os.path.expanduser(app_lock_file)
    lock = filelock.FileLock(lockfile)
    return lock


def run(*args, **kwargs):
    """Main app"""

    # define lock
    # this prevents multiple, identical circuits from running at the same time
    lock = get_lock()

    # The main app component initializes the Resilient services
    global application
    try:
        # attempt to lock file, wait 1 second for lock
        with lock.acquire(timeout=1):
            assert lock.is_locked
            application = App(*args, **kwargs)
            application.run()

    except filelock.Timeout:
        # file is probably already locked
        print("Failed to acquire lock on {0} - "
              "you may have another instance of Resilient Circuits running".format(os.path.abspath(lock.lock_file)))
    except OSError as exc:
        # Some other problem accessing the lockfile
        print("Unable to lock {0}: {1}".format(os.path.abspath(lock.lock_file), exc))
    # finally:
    #    LOG.info("App finished.")


if __name__ == "__main__":
    run()
