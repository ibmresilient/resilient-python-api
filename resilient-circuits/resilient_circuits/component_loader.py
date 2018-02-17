# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Dynamic component loader"""

import os
import sys
import logging
import traceback
import pkg_resources
from circuits import Loader, Event
from circuits.core.handlers import handler

LOG = logging.getLogger(__name__)


class load(Event):
    """yes"""
    complete = True


class load_all_failure(Event):
    """Event indicating that a component failed to load."""
    pass


class load_all_success(Event):
    """Event indicating that all components were loaded."""
    pass


def safe_but_noisy_import(name):
    modules = sys.modules.copy()
    try:
        if name in sys.modules:
            LOG.debug("Name exists in modules")
            return reload(sys.modules[name])
        else:
            LOG.debug("Name does not exist in modules")
            return __import__(name, globals(), locals(), [""])
    except Exception as exc:
        for name in sys.modules.copy():
            if name not in modules:
                del sys.modules[name]
        LOG.exception(exc)


class ComponentLoader(Loader):
    """A component to automatically load from the componentsdir directory"""

    def __init__(self, opts):
        """Initialize the loader"""
        self.opts = opts
        # Path where components should be found
        self.path = opts['componentsdir']
        # Optionally, a list of filenames that should not be loaded
        noload = opts.get("noload", "")
        self.noload = [filename.strip() for filename in noload.split(",") if filename.strip() != ""]
        super(ComponentLoader, self).__init__(init_kwargs={"opts": opts}, paths=[self.path])
        self.pending_components = []
        self.finished = False

        # Load all installed components
        installed_components = self.discover_installed_components()
        if installed_components:
            self._register_components(installed_components)

        if self.path:
            # Load all components from the components directory
            for filename in os.listdir(self.path):
                filepath = os.path.join(self.path, filename)
                if os.path.isfile(filepath) and os.path.splitext(filename)[1] == ".py":
                    cname = os.path.splitext(filename)[0]
                    if cname != "__init__":
                        if cname in self.noload:
                            LOG.info("Not loading %s", cname)
                        else:
                            LOG.info("Loading '%s' from %s", cname, filepath)
                            self.pending_components.append(cname)
                            self.fire(load(cname))
        if not self.pending_components:
            # No components from directory, we are done loading
            self.finished = True
            self.fire(load_all_success())

    def discover_installed_components(self):
        entry_points = pkg_resources.iter_entry_points('resilient.circuits.components')
        ep = None
        try:
            return [ep.load() for ep in entry_points if ep.name not in self.noload]
        except ImportError:
            LOG.error("Failed to load '%s' from '%s'", ep, ep.dist)
            raise


    def _register_components(self, component_list):
        """ register all installed components and ones from componentsdir """
        LOG.info("Loading %d components", len(component_list))
        for component_class in component_list:
            LOG.info("'%s.%s' loading", component_class.__module__, component_class.__name__)
            try:
                component_class(opts=self.opts).register(self)
                LOG.debug("'%s.%s' loaded", component_class.__module__, component_class.__name__)
            except Exception as e:
                LOG.error("Failed to load '%s.%s'", component_class.__module__, component_class.__name__, exc_info=1)
                self.fire(load_all_failure())
                return False
        return True

    @handler("exception", channel="loader")
    def exception(self, event, *args, **kwargs):
        if not self.finished:
            fevent = kwargs.get("fevent", None)
            if fevent is not None:
                cname = fevent.args[0]
                LOG.error("An exception occurred while loading component '%s'", cname)
                self.fire(load_all_failure())

    @handler("load_complete")
    def load_complete(self, event, *eargs, **ekwargs):
        """Check whether the component loaded successfully"""
        cname = event.args[0]
        if isinstance(cname, Event):
            cname = cname.args[0]

        if cname in sys.modules:
            LOG.info("Loaded and registered component '%s'", cname)
            self.pending_components.remove(cname)
            if self.pending_components == []:
                self.finished = True
                self.fire(load_all_success())
        else:
            LOG.error("Failed to load component '%s'", cname)
            safe_but_noisy_import(cname)
            self.fire(load_all_failure())
