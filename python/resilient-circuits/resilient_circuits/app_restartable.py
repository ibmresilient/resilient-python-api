#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.

# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Action Module server - restartable version of App"""

from __future__ import print_function

import logging
import os
import filelock
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .app import App
from .app import APP_CONFIG_FILE, APP_LOCK_FILE


application = None
LOG = logging.getLogger(__name__)


def log(log_level):
    logging.getLogger().setLevel(log_level)


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
        for component in self.app.components:
            if component is not self.app.action_component and component is not self.app.component_loader:
                LOG.info("stopping component %s", component)
                component.unregister()
                component.stop()

        if self.app.component_loader:
            for component in self.app.component_loader.components:
                LOG.info("stopping component %s", component)
                component.unregister()
            self.app.component_loader.unregister()

        if self.app.action_component:
            self.app.action_component.unregister()

        self.app.restarting = True
        self.app.stop()


# Main component for our application
class AppRestartable(App):
    """Our main app component, which sets up the Resilient services and other components"""

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

    def started(self, component):
        LOG.info("App Started %s", str(component))
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
        self.do_initialization()


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
        print("Failed to acquire lock on {0} - you may have another instance of Resilient Circuits running".format(APP_LOCK_FILE))
    except ValueError:
        LOG.exception("ValueError Raised. Application not running.")
    # finally:
    #    LOG.info("App finished.")


if __name__ == "__main__":
    run()
