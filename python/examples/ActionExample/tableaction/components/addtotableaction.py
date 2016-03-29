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
"""
Action to update a table field when a row is added
"""

from __future__ import print_function
import os
import logging
from copy import deepcopy


import json

import requests

from circuits import Component, Debugger
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage

from ResilientOrg import ResilientOrg as ResOrg
from ResilientOrg import ResilientIncident as ResInc

requests.packages.urllib3.disable_warnings()

# Lower the logging threshold for requests
logging.getLogger("requests.packages.urllib3").setLevel(logging.ERROR)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.Formatter('%(asctime)s:%(name)s:%(levelname)-8s %(message)s')


#log.setLevel(logging.DEBUG)  # force logging level to be DEBUG
CONFIG_DATA_SECTION = 'dtaction'
CONFIG_SOURCE_SECTION = 'resilient'
CONFIG_ACTION_SECTION = 'actiondata'


class AddToTableAction(ResilientComponent):

    """
    Action component to add a row to a table from an incident 
    """


    def __init__(self, opts):
        super(AddToTableAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        self.actiondata = opts.get(CONFIG_ACTION_SECTION, {})

        #self.sync_file = os.path.dirname(os.path.abspath(self.sync_opts.get('mapfile')))
        self.lookupfile = os.path.abspath(self.actiondata.get('lookupfile'))
        self.table_name = self.actiondata.get('tablename')

        # The queue name can be specified in the config file, or default to 'filelookup'
        self.channel = "actions." + self.options.get("queue", "dt_action")

        self.reso = ResOrg(client=self.rest_client)
        # the table definition is needed to map the columns for a row to an ID


        # setup for the manual action to add a row to the table
        self.rowmap = os.path.abspath(self.actiondata.get('rowmap'))
        self.add_table_name = self.actiondata.get("tabletoadd")


    # use the generic handler notation, as this processor handles 2 actions
    @handler("add_row_to_table")
    def _table_lookup_action(self, event, *args, **kwargs):
        """The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameters
           (event, *args, **kwargs), and ignore any messages that are not
           from the Actions module.
        """
        if not isinstance(event, ActionMessage):
            # Some event we are not interested in
            return

        log.debug("Event Name {}".format(event.name))

        # using the decorator ensures that only this event
        # will be processed
        retv = self.add_row_to_table(event)

        if retv:
            yield retv
        else:
            yield "event {} handled".format(event.name)


    def add_row_to_table(self, args):
        """
        Method invoked by manual action that adds a row to a table
        """
        log.debug("add table row")


        # get the definition of the table from the org
        table_def = self.reso.get_table_definition(self.add_table_name)

        log.debug("Table id for {} is {}".format(self.add_table_name, table_def.get('id')))

        incident = ResInc(self.reso, incident=args.message.get('incident'))

        # this is a basic template for adding a row.  A new row has no row index, so it is
        # specified with
        # {"cells":{
        #           "<cellid>":{"value":<cell value>"}, 
        #           "<cellid>":{"value":"cellvalue"},
        #            ...
        #          }
        # }

        rowtemplate = {"cells":{}}
        action_fields = args.properties               
        log.debug("argproperties {}".format(action_fields))

        for actfield in action_fields:
            log.debug(actfield)
            # use a json file to map action fields to table columns
            mapped_cell = self.get_table_column_map(actfield)
            if mapped_cell is None:
                log.error("Invalid mapping of {} to the table".format(actfield))
                raise Exception("Add Row to table feild - {} does not map to a table cell".format(actfield))

            log.debug("mapped_cell is {}".format(mapped_cell))
            mapped_id = self.get_cell_id(mapped_cell, table_def)
            log.debug("mapped id = {}".format(mapped_id))
            rowtemplate['cells'][str(mapped_id)] = {"value":action_fields.get(actfield)}

        (tablerow, ecode) = incident.add_table_row(rowtemplate, table_def.get('id'))
        if ecode is not None:
            raise Exception("Table addition failed: {}".format(ecode))
        log.debug("row added {}".format(tablerow))

        return "Row added to table"

    def get_table_column_map(self, tabcolname):
        """
        gets the mapping of the action variable to the table column name
        """
        with open(self.rowmap) as jdata:
            lookup = json.load(jdata)

        return lookup.get(tabcolname, None)

    def check_row_data(self, rowdata):
        '''
        Check the row data passed in the action message
        If there are no "value" elements in the dictionary, then the operation was
        the deletion of the field
        '''
        log.debug("check_for row data")
        for cell in rowdata.get('cells'):
            celldata = rowdata.get('cells').get(cell)
            log.debug("celldata {}".format(celldata))
            if celldata.get('value', None) is None:
                return False
        return True

    @staticmethod
    def get_cell_id(apiname, tabledef):
        '''
        map the apiname of a cell to the numeric id value.  id's are what are passed in
        to the action in the message, api_names are how we as humans view the world.
        id's are unique for a given configuration of resilient
        '''
        field = tabledef.get('fields').get(apiname, None)
        if field is not None:
            return field.get('id')
        return None

    def get_action_function(self, funcname):
        '''
        map the name passed in to a method within the object
        '''
        return getattr(self, '%s'%funcname, None)

    def lookup_data(self, lookfor):
        '''
        Lookup the passed in email address and return the name
        if there is no match, None is returned.

        The file is loaded each time the action is invoked to allow for changing
        the file content while the action processor is being run
        '''
        with open(self.lookupfile) as jdata:
            lookupdata = json.load(jdata)
        for data in lookupdata:
            if data.get('email') == lookfor:
                return data.get('name')
        return None




