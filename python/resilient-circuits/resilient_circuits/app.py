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

"""Action Module server

This uses the `Circuits <http://circuitsframework.com/>` framework to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

"""

from __future__ import print_function

import logging
import os
import filelock
from logging.handlers import RotatingFileHandler
from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits.actions_component import Actions
from circuits import Component, Debugger
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import resilient_circuits.keyring_arguments as keyring_arguments


# The run() method uses a file lock to prevent multiple simultaneous processes
# running in the same directory.  You can override the lockfile name in the
# (and so allow multiple) by setting APP_LOCK_FILE in the environment.
APP_LOCK_FILE = os.environ.get("APP_LOCK_FILE", "resilient_circuits_lockfile")


def log(log_level):
    logging.getLogger().setLevel(log_level)


# The config file location should usually be set in the environment
APP_CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "app.config")


application = None


class AppArgumentParser(keyring_arguments.ArgumentParser):
    """Helper to parse command line arguments."""
    DEFAULT_STOMP_PORT = 65001
    DEFAULT_COMPONENTS_DIR = 'components'
    DEFAULT_LOG_DIR = 'log'
    DEFAULT_LOG_LEVEL = 'INFO'
    DEFAULT_LOG_FILE = 'app.log'

    def __init__(self):
        super(AppArgumentParser, self).__init__(config_file=APP_CONFIG_FILE)
        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        default_components_dir = self.getopt("resilient", "componentsdir") or self.DEFAULT_COMPONENTS_DIR
        default_log_dir = self.getopt("resilient", "logdir") or self.DEFAULT_LOG_DIR
        default_log_level = self.getopt("resilient", "loglevel") or self.DEFAULT_LOG_LEVEL
        default_log_file = self.getopt("resilient", "logfile") or self.DEFAULT_LOG_FILE

        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")
        self.add_argument("--componentsdir",
                          type=str,
                          default=default_components_dir,
                          help="Circuits components auto-load directory")
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
        self.add_argument("--restart_on_config_change",
                          action="store_true",
                          help="Monitor config file for changes and restart")

    def parse_args(self, args=None, namespace=None):
        """Parse commandline arguments and construct an opts dictionary"""
        opts = super(AppArgumentParser, self).parse_args(args, namespace)
        if self.config:
            for section in self.config.sections():
                items = dict((item.lower(), self.config.get(section, item)) for item in self.config.options(section))
                opts.update({section: items})
        return opts



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
class App(Component):
    """Our main app component, which sets up the Resilient services and other components"""

    FILE_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
    SYSLOG_LOG_FORMAT = '%(module)s: %(levelname)s %(message)s'
    STDERR_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

    def __init__(self, auto_load_components=True):
        super(App, self).__init__()
        # Read the configuration options
        self.action_component = None
        self.component_loader = None
        self.restarting = False
        self.auto_load_components = auto_load_components
        self.do_initialization()

    def do_initialization(self):
        self.opts = AppArgumentParser().parse_args()

        self.config_logging(self.opts["logdir"], self.opts["loglevel"], self.opts['logfile'])
        LOG.info("Configuration file is %s", APP_CONFIG_FILE)
        LOG.info("Resilient user: %s", self.opts.get("email"))
        LOG.info("Resilient org: %s", self.opts.get("org"))

        self.restart_on_config_change = True if self.opts["resilient"].get("restart_on_config_change", "False").lower() in ("true", "yes", "y", "t", "1") else False
        if self.restart_on_config_change:
            LOG.info("Monitoring config file for changes.")
            event_handler = ConfigFileUpdateHandler(self)
            self.observer = Observer()
            config_dir = os.path.dirname(APP_CONFIG_FILE) or os.getcwd()

            self.observer.schedule(event_handler, path=config_dir, recursive=False)
            self.observer.daemon=True
            self.observer.start()

        # Connect to events from Action Module.
        # Note: this must be done before components are loaded, because it uses
        # each component's "channel" to initiate subscription to the message queue.
        self.action_component = Actions(self.opts)
        self.action_component.register(self)

        # Register a `loader` to dynamically load
        # all Circuits components in the 'componentsdir' directory
        if self.auto_load_components:
            LOG.info("Components auto-load directory: %s", self.opts["componentsdir"])
            self.component_loader = ComponentLoader(self.opts)
            self.component_loader.register(self)

    def config_logging(self, logdir, loglevel, logfile):
        """ set up some logging """
        global LOG_PATH, LOG
        LOG_PATH = os.path.join(logdir, logfile)

        # Ignore syslog errors from message-too-long
        logging.raiseExceptions = False

        try:
            numeric_level = getattr(logging, loglevel)
            logging.getLogger().setLevel(numeric_level)
        except AttributeError as e:
            LOG.exception("Invalid logging level specified. Using INFO level")
            logging.getLogger().setLevel(logging.INFO)

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self += Debugger()
            logging.getLogger("stomp.py").setLevel(logging.DEBUG)
        else:
            # STOMP is too noisy by default
            logging.getLogger("stomp.py").setLevel(logging.WARN)

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

        LOG = logging.getLogger(__name__)

    def _stop_observer(self):
        """ stop monitoring config file for changes """
        if self.observer:
            LOG.info("Stopping config file monitoring")
            self.observer.unschedule_all()
            self.observer.stop()

    def load_all_success(self, event):
        """OK, component loader says we're ready"""
        LOG.info("Components loaded")

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
        self._stop_observer()
        LOG.info("In stopped handler for %s", event)
        if self.restarting:
            self.restarting = False
            self._restart()
            self.run()

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
            application = App(*args, **kwargs)
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
