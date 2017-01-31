"""Dynamic component loader"""

import os
import sys
import logging
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
        
        self.path = opts['componentsdir']
        super(ComponentLoader, self).__init__(init_kwargs={"opts": opts}, paths=[self.path])
        self.pending_components = []
        self.finished = False

    @handler("registered", channel="*")
    def registered(self, component, manager):
        """Registered Event Handler"""
        if component is self:
            LOG.debug("Loader Registered")
            # Load all components from the components directory
            for filename in os.listdir(self.path):
                filepath = os.path.join(self.path, filename)
                if os.path.isfile(filepath) and os.path.splitext(filename)[1] == ".py":
                    cname = os.path.splitext(filename)[0]
                    if cname != "__init__":
                        LOG.debug("Loading %s", cname)
                        self.pending_components.append(cname)
                        self.fire(load(cname))

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
            LOG.info("Loaded component '%s'", cname)
            self.pending_components.remove(cname)
            if self.pending_components == []:
                self.finished = True
                self.fire(load_all_success())
        else:
            LOG.error("Failed to load component '%s'", cname)
            safe_but_noisy_import(cname)
            self.fire(load_all_failure())
