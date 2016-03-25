"""
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

import logging
import time

import json

import co3 as resilient


class ResilientOrg(object):
    """
    Utility class for operations against an incident and an organization
    """
    def __init__(self, client=None, opts=None):
        # when no client is passed we need to establish the connection.  However
        # to work with the circuits package the client needs to be a method/function
        # that gets called
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)

        self.enums = None
        if client:
            self.client = client  # set to the function that is passed in
        else:
            if opts is not None:
                # make the client function be
                self.client = self.get_client

                url = "https://{}:{}".format(opts.get("host", ""), opts.get("port", 443))
                self._client = resilient.SimpleClient(org_name=opts.get("org"),
                                                      proxies=opts.get("proxy"),
                                                      base_url=url,
                                                      verify=opts.get("cafile") or True)

                userinfo = self._client.connect(opts["email"], opts["password"])

                # Validate the org, and store org_id in the opts dictionary
                if(len(userinfo["orgs"])) > 1 and opts.get("org") is None:
                    raise resilient.co3.SimpleHTTPException("""
                                    User is a member of multiple organizations; please specify one.
                                    """)
                if(len(userinfo["orgs"])) > 1:
                    for org in userinfo["orgs"]:
                        if org["name"] == opts.get("org"):
                            opts["org_id"] = org["id"]
                else:
                    opts["org_id"] = userinfo["orgs"][0]["id"]
            else:
                return None


        self.GetUsers()
        self.alltasks = None
        self.groups = None


    def get_client(self):
        """
        used when the object establishes the connection to resilient instead of a client
        function being passed in a function is used, since the resilient_circuits module passes a
        function to get a client connection from its pool of connections
        """
        return self._client



    def get_phases(self):
        """
        Get the phase configuration from the org
        """
        phase = self.client().get("/phases")
        return phase

    def get_field_enums_by_type(self, ftype):
        """
        get a simple dictionary list of the field enumerations
        for a given type
        """
        fields = self.client().get('/types/{}/fields'.format(ftype))

        jstring = "{"
        for majorkey in fields:
            name = majorkey["name"].encode('ascii')
            if majorkey['values']:
                jstring += "\"{}\":[" .format(name)
                for values in majorkey["values"]:
                    label = values["label"].encode('utf-8')
                    jstring += "{{ \"{}\" : \"{}\" }}, ".format(label, values["value"])
                jstring = jstring[:-1]
                jstring += "], "

        jstring = jstring[:-1]
        jstring += "}"
        field_enums = json.loads(jstring)
        return field_enums

    # build a dictionary of just the enumerations for  incident fields.
    def get_field_enums(self):
        """
        get the field enumerations as a simple json structure of
        enumeration and id value
        """
        self.enums = self.get_field_enums_by_type('incident')
        return self.enums

    def get_incident_types(self):
        """
        get the incident type enumerations
        """
        itypes = self.client().get("/incident_types")
        return itypes


    def map_phase_id(self, pid, plist):
        """
        Map a numeric phase id to its name
        """
        self.log.debug("Phase id {}".format(pid))
        self.log.debug("Phase List {}".format(plist))
        for phase in plist.get('entities'):
            self.log.debug(phase)
            if phase.get('id') == pid:
                return phase.get('name')
        return None

    def map_phase_name_to_id(self, pname, plist):
        """
        Map a phase name to its associated id
        """
        self.log.debug("map phase name to id {}".format(pname))
        for phase in plist.get('entities'):
            self.log.debug(phase)
            if phase.get('name') == pname:
                return phase.get('id')
        return None

    def get_table_definition(self, tablename):
        """
        get the definition of a data table object based on the tables api_name
        """
        url = "/types/{}".format(tablename)
        fields = self.client().get(url)
        return fields

    def get_table_data(self, incidentid, tableid):
        """
        Tables within an incident are updated and manipulated as separate editable objects
        They are fetched from the server in separate http GET operations
        Returns a tuple
        """
        url = "/incidents/{}/table_data/{}".format(incidentid, tableid)
        self.log.debug(url)
        try:
            return (self.client().get(url), None)
        except resilient.co3.SimpleHTTPException as ecode:
            if ecode.response.status_code == 404:
                return (None, ecode.response.status_code)
            else:
                return (None, ecode)


    def GetIncidentById(self, incidentid):
        """
        Obtain the full content of an incident based on its incident id
        """
        uri = "/incidents/{}".format(incidentid)
        return self.client().get(uri)

    def GetUsers(self):
        """
        Get the users of an organization
        Used when assigning users to an incidents membership
        """
        uri = "/users"
        try:
            self.users = self.client().get(uri)
        except resilient.co3.SimpleHTTPException as ecode:
            self.log.error("Failed to get users from system {}".format(ecode))
            self.users = None
            self.log.error("Failed to get users {}".format(ecode))
            return None
        return self.users

    def GetGroups(self):
        """
        Get the groups configured in the system
        """
        uri = "/groups"
        try:
            self.groups = self.client().get(uri)
        except resilient.co3.SimpleHTTPException as ecode:
            self.log.error("Failed to get groups from system {}".format(ecode))
            self.groups = None
            return False
        return self.groups

    def GetIncidentTasks(self, incidentid):
        """
        Get the task list for a given incident.  pulls only the current list of tasks
        """
        uri = "/incidents/{}/tasktree".format(incidentid)
        try:
            itasks = self.client().get(uri)
        except resilient.co3.SimpleHTTPException as e:
            self.log.error("Failed to get incident tasks {}".format(e))
            return None

        return itasks

    def GetAllTasks(self):
        """
        Get all of the tasks in an org
        """
        uri = "/task_order"
        try:
            self.alltasks = self.client().get(uri)
        except resilient.co3.SimpleHTTPException as ecode:
            self.log.error("Failed to get all tasks {}".format(ecode))
            self.alltasks = None
        return self.alltasks

    def GetTask(self, taskid):
        """
        Get a specific tasks definition based on the task id
        """
        uri = "/tasks/{}".format(taskid)
        try:
            t = self.client().get(uri)
        except resilient.co3.SimpleHTTPException as e:
            self.log.error("Failed to get task {} \n {}".format(taskid, e))
            return None
        return t

    def PutTask(self, taskid, task):
        """
        update a task's definition
        """
        uri = "/tasks/{}".format(taskid)
        try:
            ntask = self.client().put(uri, task)
        except resilient.co3.SimpleHTTPException as ecode:
            self.log.error("Failed to update task \n{}".format(ecode))
            return None
        return ntask

    @staticmethod
    def apiname(field):
        """The full (qualified) programmatic name of a field"""
        if field["prefix"]:
            fieldname = u"{}.{}".format(field["prefix"], field["name"])
        else:
            fieldname = field["name"]
        return fieldname

    def PutCase(self, case):
        """
        update an incident and return the full data after the update
        """
        try:
            incident = self.client().put('/incidents/{}/?want_full_data=true'.format(case.get('id')), case)
            return(incident, None)
        except resilient.co3.SimpleHTTPException as ecode:
            return (None, ecode)

    def CreateCase(self, tplate):
        """
        Create a new incident in resilient based on the template provided
        Assumes that the template meets the minimum requirements for fields for a given org
        """
        self.log.debug(tplate)
        url = "/incidents/?want_full_data=true"
        self.log.debug(url)
        try:
            incident = self.client().post(url, tplate)
        except resilient.co3.SimpleHTTPException as ecode:
            return (None, ecode)

        return (incident, None)


    def PutTableRow(self, incidentid, tableid, rowdata, rowid):
        """
        update an existing row of a table within an incident
        """
        self.log.debug(rowdata)
        self.log.debug(rowid)
        url = "/incidents/{}/table_data/{}/row_data/{}".format(incidentid, tableid, rowid)
        try:
            tdata = self.client().put(url, rowdata)
            return(tdata, None)
        except resilient.co3.SimpleHTTPException as ecode:
            return(None, ecode)

    def get_incident_type_id(self, itypes, itstring):
        """
        convert from a label to the numeric value of the incident typ
        """
        for itype in itypes:
            itdict = itypes.get(itype)
            if itdict.get('name') == itstring:
                return itdict.get('id')
        return None

    def map_incident_type_id_to_name(self, itypes, typeid):
        """
        convert from an incident type id to the label
        """
        if itypes.get(str(typeid), None) is not None:
            return itypes.get(str(typeid)).get('name')
        return None


    def get_user_id(self, userlist, name):
        """
        get the specified user or group name in id format
        """
        self.log.debug("name {} >userlist {}".format(name, userlist))
        for user in userlist:
            if user.get('name') == name:
                return user.get('id')
        return None

    def CreateMilestone(self, incidentid, title, description):
        """
        create a milestone on an incident using the current time
        """
        mtemp = {"date":int(time.time()*1000),
                 "description":description,
                 "title":title}

        try:
            nmst = self.client().post("/incidents/{}/milestones".format(incidentid), mtemp)
        except resilient.co3.SimpleHTTPException as ecode:
            log.error("Resilient server error {}".format(ecode))
            return None

        return nmst

    def CreateNote(self, incident_id, content):
        """
        Create a note in an incident
        """
        note = {
            "parent_id":None,
            "mentioned_users":[],
            "text":content,
            "inc_id":incident_id,
            "id":None
        }
        nnote = self.client().post("/incidents/{}/comments".format(incident_id), note)
        return nnote

    def CreateTask(self, incident_id, taskname, instructions, phasename):
        """
        Create a task in the incident
        """
        task_template = {
            "inc_id": incident_id,
            "name": taskname,
            "phase_id": None,
            "instr_text": instructions,
            "active": True,
            "auto_task_id": None,
            "cat_name": "",
            "custom": False,
            "creator": {},
            "description": None,
            "frozen": False,
            "fullname": "Unassigned",
            "id": None,
            "inc_name": "",
            "inc_owner_id": None,
            "inc_training": False,
            "init_date": None,
            "last_update": None,
            "owner_fname": None,
            "owner_lname": None,
            "members": None,
            "perms": {},
            "regs": None,
            "required": True,
        }

        plist = self.get_phases()
        self.log.debug("Phasename {}".format(phasename))
        pid = self.map_phase_name_to_id(phasename, plist)
        self.log.debug("Phase id = {}".format(pid))
        if pid:
            task_template['phase_id'] = pid
        else:
            self.log.error("Phase name specified does not match phases defined in the system")
            return None

        ntask = self.client().post("/incidents/{}/tasks".format(incident_id), task_template)
        return ntask



