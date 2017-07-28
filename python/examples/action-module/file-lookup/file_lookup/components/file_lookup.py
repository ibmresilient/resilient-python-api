"""Action Module circuits component to lookup a value in a local CSV file"""

from __future__ import print_function
import pkg_resources
from circuits import Component, Debugger
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage
import os
import csv
import logging
LOG = logging.getLogger(__name__)

CONFIG_DATA_SECTION = 'lookup'

def config_section_data():
    """sample config data for use in app.config"""
    config_data = """[lookup]
queue=filelookup
reference_file={datafile}
source_field=custom1
dest_field=custom2
"""
    sample_file = pkg_resources.resource_filename("file_lookup", "data/sample.csv")
    return config_data.format(datafile=sample_file)

class FileLookupComponent(ResilientComponent):
    """Lookup a value in a CSV file"""

    # This component receives custom actions from Resilient and
    # executes searches in a local CSV file and stores it

    def __init__(self, opts):
        super(FileLookupComponent, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        LOG.debug(self.options)

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "filelookup")

    @handler("reload")
    def reload_options(self, event, opts):
        """Configuration options have changed, save new values"""
        LOG.info("Storing updated values from section [%s]", CONFIG_DATA_SECTION)
        self.options = opts.get(CONFIG_DATA_SECTION, {})

    @handler("lookup_value")
    def _lookup_action(self, event, *args, **kwargs):
        """The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameters
           (event, *args, **kwargs), and ignore any messages that are not
           from the Action Module.
        """
        incident = event.message["incident"]
        inc_id = incident["id"]
        source_fieldname = self.options["source_field"]
        dest_fieldname = self.options["dest_field"]
        source_value = incident["properties"].get(source_fieldname, "")

        # Open local file
        with open(self.options["reference_file"], 'r') as ref_file:
            # Lookup value in file
            reader = csv.reader(ref_file)
            value = ""
            for row in reader:
                if row[0] == source_value:
                    value = row[1]
                    break
            else:
                # Value not present in CSV file
                LOG.warning("No entry for [%s] in [%s]" % (
                    source_value,
                    self.options["reference_file"]))
                yield "field %s not updated" % dest_fieldname
                return

        LOG.info("READ %s:%s  STORED %s:%s",
                 source_fieldname, source_value,
                 dest_fieldname, value)

        def update_field(incident, fieldname, value):
            incident["properties"][fieldname] = value

        # Store value in specified incident field
        self.rest_client().get_put("/incidents/{0}".format(inc_id),
                                   lambda incident: update_field(incident, dest_fieldname, value))

        yield "field %s updated" % dest_fieldname
    #end _lookup_action
