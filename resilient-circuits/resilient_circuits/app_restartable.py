#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Action Module server - restartable version of App"""

from __future__ import print_function

import logging
import os

import filelock
from circuits import Event, Timer
from resilient_circuits.app import (App, AppArgumentParser,
                                    RotatingFileHandler, constants, get_lock,
                                    helpers)
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import resilient

application = None
LOG = logging.getLogger(__name__)


class reload(Event):
    """Notify components of updates to config"""
    complete = True

    def __init__(self, opts):
        super(reload, self).__init__(opts=opts)
        self.opts = opts


class ConfigFileUpdateHandler(PatternMatchingEventHandler):
    """ Restarts application when config file is modified """

    def __init__(self, app):
        super(ConfigFileUpdateHandler, self).__init__()
        self.app = app
        self.max_reload_time = 30

    @classmethod
    def set_patterns(cls, config_file):
        cls.patterns = ["*" + os.path.basename(config_file), ]

    def on_modified(self, event):
        """ For 'FileModifiedEvent' events, initiate reload of data from config file and restart components.  """

        self.reload_config()

    def on_created(self, event):
        """ For 'FileCreatedEvent' events, initiate reload of data from config file and restart components.

        Triggered by certain editors such as 'vi', which will recreate rather than modify the config file,
        when updating.

        """

        self.reload_config()

    def reload_config(self):
        """ Reload data from config file and restart components. """

        if self.app.reloading:
            LOG.warning("Configuration file change ignored because reload already in progress")
            return

        LOG.info("Configuration file has changed! Notify components to reload")
        self.app.reloading = True
        opts = helpers.get_configs(path_config_file=self.app.config_file, ALLOW_UNRECOGNIZED=self.app.ALLOW_UNRECOGNIZED)
        # See if we need to reset root loglevel on reload
        self.reset_loglevel(opts)
        # check if we need to reset rotating file handler opts
        self.reset_filehandler(opts)
        reload_event = reload(opts=opts)
        self.app.reload_timer = Timer(self.max_reload_time, Event.create("reload_timeout"))
        self.app.fire(reload_event)
        self.app.reload_timer.register(self.app)

    def reset_loglevel(self, opts):
        """ Reset the loglevel if it has changed in the config file. """

        # Get loglevel setting from app.config.
        config_loglevel = opts.get("loglevel", None)

        # If loglevel setting is configured.
        if config_loglevel:
            # Check if it's a valid setting
            if hasattr(logging, config_loglevel.upper()):
                # Get root logger instance
                root_logger = logging.getLogger()
                # If level is different set loglevel to new value.
                if logging.getLevelName(root_logger.level) != config_loglevel.upper():
                    root_logger.setLevel(config_loglevel.upper())
            else:
                LOG.error("Invalid app.config setting for loglevel %s", config_loglevel)

    def reset_filehandler(self, opts):
        """
        Reset ``log_max_bytes`` and ``log_backup_count`` if changed on reload
        """

        log_max_bytes = opts.get(constants.APP_CONFIG_LOG_MAX_BYTES)
        log_backup_count = opts.get(constants.APP_CONFIG_LOG_BACKUP_COUNT)

        # loop through handlers and find the RotatingFileHandler
        # (it will be there -- just need to find it in the list)
        handlers = getattr(logging.getLogger(), "handlers", [])
        for handler in handlers:
            if isinstance(handler, RotatingFileHandler):

                # update values as appropriate
                if log_backup_count is not None and handler.backupCount != log_backup_count:
                    LOG.debug("Reloaded 'log_backup_count' to '%s'",log_backup_count)
                    handler.backupCount = log_backup_count
                if log_max_bytes is not None and handler.maxBytes != log_max_bytes:
                    LOG.debug("Reloaded 'log_max_bytes' to '%s'", log_max_bytes)
                    handler.maxBytes = log_max_bytes
                break # break the loop as we only needed the RotatingFileHandler

# Main component for our application
class AppRestartable(App):
    """Our main app component, which sets up the Resilient services and other components"""

    def __init__(self, *args, **kwargs):
        super(AppRestartable, self).__init__(*args, **kwargs)
        self.reloading = False
        self.reload_timer = None
        self.observer = None

    def do_initialize_watchdog(self):
        """Initialize the configuration file watchdog"""
        # Monitor the configuration file, using a Watchdog observer daemon.
        LOG.info("Monitoring config file for changes.")
        ConfigFileUpdateHandler.set_patterns(self.config_file)
        event_handler = ConfigFileUpdateHandler(self)
        self.observer = Observer()
        config_dir = os.path.dirname(self.config_file)
        if not config_dir:
            config_dir = os.getcwd()
        self.observer.schedule(event_handler, path=config_dir, recursive=False)
        self.observer.daemon = True
        self.observer.start()

    def started(self, component):
        LOG.info("App Started %s", str(component))
        self.do_initialize_watchdog()

    def stopped(self, component):
        """Stopped Event Handler"""
        LOG.info("App Stopped")
        self._stop_observer()

    def reload_complete(self, event, *args, **kwargs):
        """ All components done handling reload event """
        if event.parent.success:
            LOG.info("Reload completed successfully!")
        else:
            LOG.error("Reloading failed to complete successfully!")
        if self.reload_timer:
            self.reload_timer.unregister()
            self.reload_timer = None
        self.reloading = False

    def reload_timeout(self, event):
        """Reload timed out, assume it failed"""
        LOG.error("Reload Timed Out, Assuming Failure!")
        self.reloading = False

    def _stop_observer(self):
        """ stop monitoring config file for changes """
        if self.observer:
            LOG.info("Stopping config file monitoring")
            self.observer.unschedule_all()
            self.observer.stop()
            self.observer = None


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
            application = AppRestartable(*args, **kwargs)
            application.run()

    except filelock.Timeout:
        # file is probably already locked
        errmsg = ("Failed to acquire lock on {0} - you may have "
                  "another instance of Resilient Circuits running")
        print(errmsg.format(os.path.abspath(lock.lock_file)))
    except ValueError:
        LOG.exception("ValueError Raised. Application not running.")
    except OSError as exc:
        # Some other problem accessing the lockfile
        print("Unable to lock {0}: {1}".format(os.path.abspath(lock.lock_file), exc))
    # finally:
    #    LOG.info("App finished.")


if __name__ == "__main__":
    run()
