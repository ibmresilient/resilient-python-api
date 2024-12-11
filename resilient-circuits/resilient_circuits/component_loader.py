# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.
# pragma pylint: disable=line-too-long

"""Dynamic component loader"""

import os
import sys
import logging
import pkg_resources
from circuits import Loader, Event
from circuits.core.handlers import handler
from resilient_circuits.stomp_events import SubscribeLowCode
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


def safe_but_noisy_import(cname):
    modules = sys.modules.copy()
    try:
        if cname in sys.modules:
            LOG.debug("Name exists in modules")
            # TODO reload not found
            return reload(sys.modules[cname])

        LOG.debug("Name does not exist in modules")
        return __import__(cname, globals(), locals(), [""])
    except Exception as exc:
        for name in sys.modules.copy():
            if name not in modules:
                del sys.modules[name]
        LOG.exception(exc)


class ComponentLoader(Loader):
    """A component to automatically load from the componentsdir directory"""

    def __init__(self, opts, connector_queues=None):
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

        additional_connector_queues = connector_queues if connector_queues else []
        self.register_components(additional_connector_queues)

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

    def discover_installed_components(self, entry_points):
        entry_points = pkg_resources.iter_entry_points(entry_points)
        ep = None
        try:
            return_list = []
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

                    return_list.append(cmp_class)
            return return_list

        except ImportError as e:
            LOG.error("Failed to load '%s' from '%s'", ep, ep.dist)
            raise e

    def register_components(self, connector_queues):
        """find all the installed apps and register the component classes to handle messages

        :param connector_queues: list of additional queues to include for the low_code app
        :type connector_queues: list
        """
        # Load all installed components
        installed_components = self.discover_installed_components("resilient.circuits.components")
        bg_installed_components = self.discover_installed_components("resilient.circuits.background")
        self.lc_assign_queues(bg_installed_components, connector_queues)
        # combine lists for registration
        installed_components.extend(bg_installed_components)

        # clear any existing registrations
        for component in list(self.components):
            self.unregisterChild(component)

        if installed_components:
            self._register_components(installed_components)

        # start the STOMP listeners for these new queues
        for queue in connector_queues:
            self.fire(SubscribeLowCode(queue))

    def _register_components(self, component_list):
        """ register all installed components and ones from componentsdir """
        LOG.info("Loading %d components", len(component_list))
        for component_class in component_list:
            LOG.info("'%s.%s' loading", component_class.__module__, component_class.__name__)
            try:
                component_class(opts=self.opts).register(self)
                LOG.debug("'%s.%s' loaded", component_class.__module__, component_class.__name__)
            except Exception as e:
                LOG.error("Failed to load '%s.%s' (%s)", component_class.__module__, component_class.__name__, e, exc_info=1)
                self.fire(load_all_failure())
                return False
        return True

    def lc_assign_queues(self, cmp_class_list, low_code_queues, handler_type=constants.LOW_CODE_HANDLER_VAR):
        """for a list of app components, assign low_code queues to those components
             which are used by the low_code app

        :param cmp_class_list: list of potential components for handler assignment
        :type cmp_class_list: list
        :param low_code_queues: list of queues to assign to components
        :type low_code_queues: list
        :param handler_type: type of component to filter on
        :type handler_type: str
        """
        # get low code queues names
        subscription_queue = self.lc_get_subscription_queue()

        if subscription_queue:
            low_code_queue_names = tuple(set(low_code_queues + [subscription_queue])) # remove duplicates
        else:
            low_code_queue_names = tuple(low_code_queues)

        for cmp_class in cmp_class_list:
            # handle all low code handlers
            for lc_handler in helpers.get_handlers(cmp_class, handler_type=handler_type):
                self.lc_update_handlers(lc_handler, low_code_queue_names)

    @handler("add_new_queue", channel="loader")
    def event_add_new_queues(self, new_queues):
        """ when new low code queues are created and a subscription message is received,
                assign them to the low code app component

        :param new_queues: list of new queues
        :type new_queues: list
        """
        return self.register_components(new_queues)

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
            if not self.pending_components:
                self.finished = True
                self.fire(load_all_success())
        else:
            LOG.error("Failed to load component '%s'", cname)
            # this logic is broken as the reload function is undefined
            #safe_but_noisy_import(cname)
            self.fire(load_all_failure())

    def lc_get_subscription_queue(self):
        """
            Get the subscription queue.
            The subscription queue publishes new/removed connector queues
            :return subscription queue name
            :rtype: str
        """

        # the subscription queue is an environment variable
        subscription_queue = os.environ.get(constants.ENVVAR_LOWCODE_SUBSCRIPTION_QUEUE)
        LOG.info("subscription queue: %s", subscription_queue)

        return subscription_queue

    def lc_update_handlers(self, lc_handler, lc_queues):
        """ Update the queue names associated with the low code handler

        :param lc_handler: Low Code Handler
        :type lc_handler:
        :param lc_queues: new queues to add to low code handlers
        :type lc_queues: tuple
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
        # TODO how to handle unsubscribe message types
        LOG.info("Adding new queues: %s with existing queues: %s to handler: %s", lc_queues, lc_names, lc_handler)

        lc_handler_obj.names = tuple(set(lc_names + lc_queues)) # remove duplicates

        # if no names provided we need to disable the handler otherwise it will listen on all queues
        # this is for a case where a low code handler exists in the components that are registered
        # but there are no low code queues to listen to
        if not lc_names:
            LOG.warning("Low code handler for function '%s' in module '%s' was loaded but had no queues to subscribe to. Disabling handler...", lc_handler_obj.__name__, lc_handler_obj.__module__)
            lc_handler_obj.handler = False
