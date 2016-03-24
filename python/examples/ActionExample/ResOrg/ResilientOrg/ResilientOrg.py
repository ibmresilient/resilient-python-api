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

import co3 as resilient
import os
import json
from collections import OrderedDict
from pprint import pprint

import logging
import time

# Object class for dealing with the resilient organization 

class ResilientOrg(object):
    def __init__(self,client=None,opts=None):
        # when no client is passed we need to establish the connection.  However
        # to work with the circuits package the client needs to be a method/function that gets called
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
                    raise Exception("User is a member of multiple organizations; please specify one.")
                if(len(userinfo["orgs"])) > 1:
                    for org in userinfo["orgs"]:
                        if org["name"] == opts.get("org"):
                            opts["org_id"] = org["id"]
                else:
                    opts["org_id"] = userinfo["orgs"][0]["id"]                
            else:
                return None


        self.GetUsers()


    def get_client(self):
        # used when the object establishes the connection to resilient instead of a client function being passed in
        # a function is used, since the resilient_circuits module passes a function to get a client connection from 
        # its pool of connections
        return self._client


    def get_phases(self):
        phase = self.client().get("/phases")
        return phase

    # build a dictionary of just the enumerations for  incident fields.
    def get_field_enums(self):
        self.enums = get_field_enums_by_type('incident')
        return self.enums

    def get_incident_types(self):
        t = self.client().get("/incident_types")
        return t


    def map_phase_id(self,pid,plist):
        self.log.debug("Phase id {}".format(pid))
        self.log.debug("Phase List".format(plist))
        for p in plist.get('entities'):
            self.log.debug(p)
            if p.get('id') == pid:
                return p.get('name')
        return None

    # build dictionary of fields for a specific DTO definition
    def get_field_enums_by_type(self,ftype):
        fields = self.client().get('/types/{}/fields'.format(ftype))

        jstring = "{"  
        for majorkey in fields:
            name = majorkey["name"].encode('ascii')
            if majorkey['values']:
                jstring += "\"{}\":[" .format(name)
                for values in majorkey["values"]:
                    label = values["label"].encode('utf-8')
                    jstring += "{{ \"{}\" : \"{}\" }},".format(label,values["value"])
                jstring = jstring[:-1]
                jstring += "],"

        jstring = jstring[:-1]
        jstring += "}"
        js = json.loads(jstring)
        return js


    # get the definition of a data table object based on the tables api_name
    def get_table_definition(self,tablename):
        url = "/types/{}".format(tablename)
        fields = self.client().get(url)
        return fields

    def get_table_data(self,incidentid,tableid):
        '''
        Tables within an incident are updated and manipulated as separate editable objects
        They are fetched from the server in separate http GET operations
        Returns a tuple 
        '''
        url = "/incidents/{}/table_data/{}".format(incidentid,tableid)
        self.log.debug(url)
        try:
            return (self.client().get(url),None)
        except Exception as e:
            if e.response.status_code == 404:
                return (None,e.response.status_code)
            else:
                return (None,e)

    def get_enums(self):
        if self.enums is None:
            self.enums = self.get_field_enums()
        return self.enums

    def GetIncidentById(self,incidentid):
        '''
        Obtain the full content of an incident based on its incident id
        '''
        uri = "/incidents/{}".format(incidentid)
        return self.client().get(uri)

 
    def GetUsers(self):
        '''
        Get the users of an organization 
        Used when assigning users to an incidents membership
        '''
        uri = "/users"
        try:
            self.users = self.client().get(uri)
        except Exception as e:
            self.users = None
            self.log.error("Failed to get users {}".format(e))
            return None
        return self.users

    def GetGroups(self):
        uri = "/groups"
        try:
            self.groups = self.client().get(uri)
        except Exception as e:
            self.groups = None
            return False
        return self.groups

    def GetIncidentTasks(self,incidentid):
        '''
        Get the task list for a given incident.  pulls only the current list of tasks
        '''
        uri = "/incidents/{}/tasktree".format(incidentid)
        try:
            itasks = self.client().get(uri)
        except Exception as e:
            self.log.error("Failed to get incident tasks {}".format(e))
            return None

        return itasks

    def GetAllTasks(self):
        '''
        Get all of the tasks in an org
        '''
        uri = "/task_order"
        try:
            self.alltasks = self.client().get(uri)
        except Exception as e:
            self.log.error("Failed to get all tasks {}".format(e))
            self.alltasks = None
        return self.alltasks

    def GetTask(self,taskid):
        '''
        Get a specific tasks definition based on the task id
        '''
        uri = "/tasks/{}".format(taskid)
        try:
            t = self.client().get(uri)
        except Exception as e:
            self.log.error("Failed to get task {} \n {}".format(taskid,e))
            return None
        return t

    def PutTask(self,taskid,task):
        '''
        update a task's definition
        '''
        uri = "/tasks/{}".format(taskid)
        try:
            t = self.client().put(uri,task)
        except Exception as e:
            self.log.error("Failed to update task \n{}".format(e))
            return None
        return t

    @staticmethod
    def apiname(field):
        """The full (qualified) programmatic name of a field"""
        if field["prefix"]:
            fieldname = u"{}.{}".format(field["prefix"], field["name"])
        else:
            fieldname = field["name"]
        return fieldname

    def PutCase(self,case):
        '''
        update an incident and return the full data after the update
        '''
        try:
            incident = self.client().put('/incidents/{}/?want_full_data=true'.format(case.get('id')), case)
            exceptcode = None
            return(incident,exceptcode)
        except Exception as e:
            exceptcode = e
            return (None,exceptcode)

    def CreateCase(self,tplate):
        '''
        Create a new incident in resilient based on the template provided
        Assumes that the template meets the minimum requirements for fields for a given org
        '''
        self.log.debug(tplate)
        url = "/incidents/?want_full_data=true"
        self.log.debug(url)
        try:
            incident = self.client().post(url, tplate)
            exceptcode = None
        except Exception as e:
            exceptcode = e
            return (None,exceptcode)

        return (incident,None)


    def PutTableRow(self,incidentid,tableid,rowdata,rowid):
        '''
        update an existing row of a table within an incident
        '''
        self.log.debug(rowdata)
        self.log.debug(rowid)
        url = "/incidents/{}/table_data/{}/row_data/{}".format(incidentid,tableid,rowid)
        try:
            td = self.client().put(url,rowdata)
            return(td,None)
        except Exception as e:
            return(None,e)

    def get_incident_type_id(self,itypes,itstring):
        for it in itypes:
            itdict = itypes.get(it)
            if itdict.get('name') == itstring:
                return itdict.get('id')
        return None

    def map_incident_type_id_to_name(self,itypes,id):
        if itypes.get(str(id),None) is not None:
            return itypes.get(str(id)).get('name')
        return None


    def get_user_id(self,userlist,name):
        self.log.debug("name {} >userlist {}".format(name,userlist))
        for user in userlist:
            if user.get('name') == name:
                return user.get('id')
        return None

    def CreateMilestone(self,incidentid,title,description):
        mtemp = {"date":int(time.time()*1000),
                 "description":description,
                 "title":title}

        nmst = self.client().post("/incidents/{}/milestones".format(incidentid),mtemp)
        return nmst