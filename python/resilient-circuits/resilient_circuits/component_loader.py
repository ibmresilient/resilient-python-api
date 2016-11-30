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
#
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
        # Path where components should be found
        self.path = opts['componentsdir']
        # Optionally, a list of filenames that should not be loaded
        noload = opts.get("noload", "")
        self.noload = [filename.strip() for filename in noload.split(",") if filename.strip() != ""]
        super(ComponentLoader, self).__init__(init_kwargs={"opts": opts}, paths=[self.path])
        self.pending_components = []
        self.finished = False

    @handler("started", channel="*")
    def started(self, event, component):
        """Started Event Handler"""
        LOG.debug("Started")
        # Load all components from the components directory
        for filename in sorted(os.listdir(self.path)):
            filepath = os.path.join(self.path, filename)
            if os.path.isfile(filepath) and os.path.splitext(filename)[1] == ".py":
                cname = os.path.splitext(filename)[0]
                if cname != "__init__":
                    if cname in self.noload:
                        LOG.info("Not loading %s", cname)
                    else:
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
