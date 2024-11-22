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
from resilient_circuits import constants, helpers

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

    def __init__(self, opts, connector_queues=[]):
        """Initialize the loader"""

        """ connector_queues is list of additional connector queues to subscribe to"""

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
        installed_components = self.discover_installed_components(connector_queues)
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

    def discover_installed_components(self, new_queues=[]):
        """
        :param new_queues: list of new low code queues to subscribe to. This is useful for connector queues which
                            we will get info on from /connectors/queues endpoint or from a main subscription
                            queue for low code
        :type new_queues: list[str]
        """
        entry_points = pkg_resources.iter_entry_points('resilient.circuits.components')
        ep = None
        try:
            return_list = []

            # get low code queues names
            low_code_queue_names = self.get_all_lc_queues(new_queues)

            # Loop entry points
            for ep in entry_points:
                if ep.name not in self.noload:

                    # Load the component class
                    cmp_class = ep.load()

                    # Get the class' __module__ name
                    # Note: the name used for the app.config section of this app should be the same as the __module__
                    cmp_module_name = cmp_class.__module__.split(".")[0]

                    # If an INBOUND_MSG_APP_CONFIG_Q_NAME is defined in the app.config in the section for this app, use it
                    custom_q_name = self.opts.get(cmp_module_name, {}).get(constants.INBOUND_MSG_APP_CONFIG_Q_NAME, "")

                    if custom_q_name:
                        # Get the inbound_handlers in this component and overwrite their 'channel' and 'names' attributes
                        inbound_handlers = helpers.get_handlers(cmp_class, handler_type="inbound_handler")
                        for ih in inbound_handlers:

                            new_channel = "{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, custom_q_name)
                            new_names = (custom_q_name, )

                            if sys.version_info.major < 3:
                                # Handle PY < 3
                                ih[1].__func__.channel = new_channel
                                ih[1].__func__.names = new_names
                            else:
                                # Handle PY >= 3 specific imports
                                ih[1].channel = new_channel
                                ih[1].names = new_names

                    # handle all low code handlers
                    for lc_handler in helpers.get_handlers(cmp_class, handler_type=constants.LOW_CODE_HANDLER_VAR):
                        self.update_low_code_handlers(lc_handler, low_code_queue_names)

                    return_list.append(cmp_class)
            return return_list

        except ImportError as e:
            LOG.error("Failed to load '%s' from '%s'", ep, ep.dist)
            raise e

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

    def get_all_lc_queues(self, lc_new_queues):
        """
        Put all the low code connector queues together. As of now, this may come from app.config or from a subscription queue method.

        :returns: tuple with the names of the queues to add to the low code handler
        """
        # TODO: low code queues might change depending on how we decide to consume the low code queue names
        # get all the low code queues from app.config (LIKELY TO CHANGE)
        low_code_queues = self.opts.get(constants.LOW_CODE_QUEUES_LIST_APP_CONFIG, "")
        lc_names_from_config = tuple(low_code_queues.split(",")) if low_code_queues else ()

        # Any new connector queues that were discovered from the main subscription queue; we need it as a tuple to add to the handler
        lc_new_queues = tuple(lc_new_queues) if lc_new_queues else ()

        return tuple(set(lc_names_from_config + lc_new_queues)) # remove duplicates

    def update_low_code_handlers(self, lc_handler, lc_queues):
        """ Update the queue names associated with the low code handler

        :param lc_handler: Low Code Handler
        :type lc_handler: 
        :param lc_names_from_config: low code queue names that are stored in constants.LOW_CODE_QUEUES_LIST_APP_CONFIG
        :type lc_names_from_config: tuple
        :param lc_new_queues: 
        :type lc_new_queues: tuple
        """
        if sys.version_info.major < 3:
            # Handle PY < 3
            lc_handler_obj = lc_handler[1].__func__
        else:
            # Handle PY >= 3 specific imports
            lc_handler_obj = lc_handler[1]

        # extend '.names' tuple with any additional queue names from the config
        lc_names_from_handler = lc_handler_obj.names or ()
        lc_names = lc_names_from_handler
        lc_names = lc_names + lc_queues
        lc_handler_obj.names = tuple(set(lc_names)) # remove duplicates

        # if no names provided we need to disable the handler otherwise it will listen on all queues
        # this is for a case where a low code handler exists in the components that are registered
        # but there are no low code queues to listen to
        if not lc_names:
            LOG.debug("Low code handler for function '%s' in module '%s' was loaded but had no queues to subscribe to. Disabling handler...", lc_handler_obj.__name__, lc_handler_obj.__module__)
            lc_handler_obj.handler = False