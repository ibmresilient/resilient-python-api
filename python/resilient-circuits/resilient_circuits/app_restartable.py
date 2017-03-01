#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Action Module server - restartable version of App"""

from __future__ import print_function

import logging
import os
import filelock
from circuits.core.handlers import handler
from circuits import Event, Timer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from resilient_circuits.app import App
from resilient_circuits.app import APP_CONFIG_FILE, APP_LOCK_FILE


application = None
LOG = logging.getLogger(__name__)


def log(log_level):
    logging.getLogger().setLevel(log_level)


class begin_restart(Event):
    pass


class ConfigFileUpdateHandler(PatternMatchingEventHandler):
    """ Restarts application when config file is modified """
    patterns = ["*" + os.path.basename(APP_CONFIG_FILE), ]

    def __init__(self, app):
        super(ConfigFileUpdateHandler, self).__init__()
        self.app = app

    def on_modified(self, event):
        """ reload data from config file and restart components """
        LOG.info("configuration file has changed! restarting all components!")
        self.app._stop_observer()

        # We need to shut things down in the right order
        if self.app.component_loader:
            # This will unregister all the components registered to it as well
            LOG.info("unregistering component %s", self.app.component_loader)
            self.app.component_loader.unregister()

        if self.app.action_component:
            LOG.info("unregistering component %s", self.app.action_component)
            self.app.action_component.unregister()

        for component in self.app.components:
            # The Actions component and the Debugger, if attached
            if component is not self.app.action_component and component is not self.app.component_loader:
                LOG.info("unregistering component %s", component)
                component.unregister()


# Main component for our application
class AppRestartable(App):
    """Our main app component, which sets up the Resilient services and other components"""

    def __init__(self, *args, **kwargs):
        super(AppRestartable, self).__init__(*args, **kwargs)
        self.component_collection = []

    def do_initialize_watchdog(self):
        """Initialize the configuration file watchdog"""
        self.restarting = False

        # Monitor the configuration file, using a Watchdog observer daemon.
        LOG.info("Monitoring config file for changes.")
        event_handler = ConfigFileUpdateHandler(self)
        self.observer = Observer()
        config_dir = os.path.dirname(APP_CONFIG_FILE) or os.getcwd()
        self.observer.schedule(event_handler, path=config_dir, recursive=False)
        self.observer.daemon = True
        self.observer.start()

    def begin_restart(self):
        LOG.info("Beginning Restart Procedure")
        self.restarting = True
        self.stop()

    def started(self, component):
        LOG.info("App Started %s", str(component))

    def load_all_success(self, event):
        for component in self.components:
            LOG.debug("Adding %s to restartable app components list",
                      str(component))
            self.component_collection.append(component)

        self.do_initialize_watchdog()

    def stopped(self, component):
        """Stopped Event Handler"""
        LOG.info("App Stopped")
        self._stop_observer()
        if self.restarting:
            self.restarting = False
            self._restart()
            self.run()

    def _stop_observer(self):
        """ stop monitoring config file for changes """
        if self.observer:
            LOG.info("Stopping config file monitoring")
            self.observer.unschedule_all()
            self.observer.stop()
            self.observer = None

    def _restart(self):
        """ Restart Event Handler """
        LOG.info("Restarting")
        logging.getLogger().handlers = []
        self.component_collection = []
        self.do_initialization()

    @handler("unregistered")
    def unregistered(self, component, manager):
        """ Handler for unregistered notificatons for all App subcomponents """
        LOG.info("%s has unregistered from %s.", str(component), str(manager))

        if component in self.component_collection:
            self.component_collection.remove(component)

            if len(self.component_collection) == 0:
                # All are stopped
                self.fire(begin_restart())
            else:
                LOG.debug("Still waiting on %s to stop.",
                          self.component_collection)


def run(*args, **kwargs):
    """Main app"""

    # define lock
    # this prevents multiple, identical circuits from running at the same time
    lock = filelock.FileLock(APP_LOCK_FILE)

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
        print(errmsg.format(APP_LOCK_FILE))
    except ValueError:
        LOG.exception("ValueError Raised. Application not running.")
    # finally:
    #    LOG.info("App finished.")


if __name__ == "__main__":
    run()
