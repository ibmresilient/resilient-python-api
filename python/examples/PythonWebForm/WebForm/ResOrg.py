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

import os
import json

import co3 as resilient
from WebForm import app

"""
Utility module
"""

# Object class for dealing with the resilient organization 

class ResOrg(object):
    """
    utility object
    """
    def __init__(self):
        self.config = app.config
        self.form_config = None

        config = self.config
        self.client = resilient.SimpleClient(org_name=config['RES_ORG'], 
            base_url="https://{}:{}".format(config['RES_HOST'], config['RES_PORT']), verify=config['RES_CA'])
        self.client.connect(config['RES_ID'], config['RES_PW'])
        self.enums = None
        self.enums = self.get_field_enums()
        self.form_config = self.get_form_config()
        self.create_template = None
        self.create_template =self.get_template('CreateTemplate')


    # build a dictionary of just the enumerations for fields.
    def get_field_enums(self):
        """
        get the field enumerations for the incident type for mapping
        """
        if self.enums is None:
            fields = self.client.get('/types/incident/fields')
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
            self.enums = json.loads(jstring)
            return self.enums
        return self.enums

    # read the configuration for the input form
    def get_form_config(self):
        """ read the configuration file for the input form"""
        if self.form_config is None:
            aproot = os.path.dirname(os.path.abspath(__file__))
            formfile = os.path.join(aproot, 'config', 'form_layout.json')
            with open(formfile, 'rb') as ffconfig:
                self.form_config = json.load(ffconfig)

        return self.form_config

    def get_enums(self):
        """ get the field enumerations"""
        if self.enums is None:
            self.enums = self.get_field_enums()

        return self.enums

    def get_template(self, tempname):
        """
        Read the template for incident creation
        """
        if self.create_template is None:
            aproot = os.path.dirname(os.path.abspath(__file__))
            formfile = os.path.join(aproot, 'config', tempname+'.json')
            with open(formfile, 'rb') as ffinput:
                template  = json.load(ffinput)
        return template


    def get_config(self, configelement):
        """
        Get the configuration 
        """
        for i in self.form_config:
            if i.get('fieldname', None) == configelement:
                return i
        return None

