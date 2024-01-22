#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Action Module server

This uses the `Circuits <http://circuitsframework.com/>` framework to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

"""

from __future__ import print_function

import logging
from logging.handlers import RotatingFileHandler
from six import string_types, PY3
import re
import os
import filelock
from circuits import Manager, BaseComponent, Component, Debugger, Loader
from resilient import get_config_file
from resilient import constants as resilient_constants
from resilient_circuits import constants, helpers
from resilient_circuits.app_argument_parser import AppArgumentParser
from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits.actions_component import Actions, ResilientComponent


application = None
logging_initialized = False


class RedactingFilter(logging.Filter):
    """ Redacting logging filter to prevent Resilient circuits sensitive password values from being logged.

    """
    def __init__(self):
        super(RedactingFilter, self).__init__()

    def filter(self, record):
        try:
            # Best effort regex filter pattern to redact password logging.
            if PY3: # struggles to convert unicode dicts in PY2 -- so PY3 only
                record.msg = str(record.msg)
            if isinstance(record.msg, string_types):
                pattern = "|".join(constants.PASSWORD_PATTERNS)
                # see https://regex101.com/r/ssoH91 for detailed test
                # this is the more performant version where only one regex is checked
                regex = re.compile(r"""
                    ((?:{0})       # start capturing group for password pattern from constants.PASSWORD_PATTERNS
                    \w*?[\'\"]?    # match any word characters (lazy) and zero or one quotation marks
                    \W*?u?[\'\"]   # match any non-word characters (lazy) up until exactly one quotation mark
                                   # and potentially a u'' situation for PY27
                                   # (this quotation mark indicates the beginning of the secret value)
                    )              # end first capturing group
                    (.*?)          # capture the problematic content (lazy capture up until end quotation mark)
                    ([\'\"])       # capturing group to end the regex match
                """.format(pattern), re.X)

                # keep first and third capturing groups, but replace inner group with "***"
                record.msg = regex.sub(r"\1***\3", record.msg)
        except Exception:
            return True

        return True


# Main component for our application
class App(Component):
    """Our main app component, which sets up the Resilient services and other components"""

    FILE_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] [%(threadName)s] %(message)s'
    SYSLOG_LOG_FORMAT = '%(module)s: %(levelname)s %(message)s'
    STDERR_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] [%(threadName)s] %(message)s'

    def __init__(self, auto_load_components=True, config_file=None, ALLOW_UNRECOGNIZED=False, IS_SELFTEST=False):
        super(App, self).__init__()
        # Read the configuration options
        self.ALLOW_UNRECOGNIZED = ALLOW_UNRECOGNIZED
        resilient_constants.ALLOW_UNRECOGNIZED = ALLOW_UNRECOGNIZED
        self.IS_SELFTEST = IS_SELFTEST
        self.action_component = None
        self.component_loader = None
        self.auto_load_components = auto_load_components
        self.config_file = config_file or get_config_file()
        self.do_initialization()

    def do_initialization(self):
        self.opts = helpers.get_configs(path_config_file=self.config_file, ALLOW_UNRECOGNIZED=self.ALLOW_UNRECOGNIZED)

        self.config_logging(self.opts["logdir"], self.opts["loglevel"], self.opts["logfile"], self.opts[constants.APP_CONFIG_LOG_MAX_BYTES], self.opts[constants.APP_CONFIG_LOG_BACKUP_COUNT])
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
        LOG.info("App Config plugin: %s", self.opts.pam_plugin.__class__.__name__ if self.opts.pam_plugin else "None")
        if self.opts.get("test_actions", False):
            # Make all components aware that we are in test mode
            ResilientComponent.test_mode = True

        # Make all components aware that we are in selftest mode
        ResilientComponent.IS_SELFTEST = self.IS_SELFTEST

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

    def config_logging(self, logdir, loglevel, logfile, log_max_bytes, log_backup_count):
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

        LOG.addFilter(RedactingFilter())

        file_handler = RotatingFileHandler(LOG_PATH, maxBytes=log_max_bytes,
                                           backupCount=log_backup_count)
        file_handler.setFormatter(logging.Formatter(self.FILE_LOG_FORMAT))
        file_handler.addFilter(RedactingFilter())
        logging.getLogger().addHandler(file_handler)

        syslog = logging.handlers.SysLogHandler()
        syslog.setFormatter(logging.Formatter(self.SYSLOG_LOG_FORMAT))
        syslog.addFilter(RedactingFilter())
        logging.getLogger().addHandler(syslog)

        stderr = logging.StreamHandler()
        stderr.setFormatter(logging.Formatter(self.STDERR_LOG_FORMAT))
        stderr.addFilter(RedactingFilter())
        logging.getLogger().addHandler(stderr)

        if LOG.getEffectiveLevel() == logging.DEBUG:
            self += Debugger(logger=LOG)

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
