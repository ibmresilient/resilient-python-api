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
Methods and functions for building the dynamic web form and for handling 
the creation of an incident
"""

import datetime
import time
import re
from copy import deepcopy
from pprint import pprint

from WebForm import app
from flask import render_template, request, redirect, url_for, g, session, flash
import wtforms as wtf
import wtforms.widgets.core

from .forms import LoginForm, CaseForm, DatePickerWidget, DateTimePickerWidget

from .ResOrg import ResOrg

# allows specifying width and height in creation
# wtforms default TextArea requires that you specify the width and height in the
# jinja 2 template
class TextArea(wtforms.widgets.core.TextArea):
    """
    enhancement of text area widget to allow for height and width
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, field, **kwargs):
        for arg in self.kwargs:
            if arg not in kwargs:
                kwargs[arg] = self.kwargs[arg]
        return super(TextArea, self).__call__(field, **kwargs)


# Simple function to create the form dynamically
# Needs to have validation etc added to the form fields
def build_form():
    """
    Function to build the form
    """
    if getattr(g, 'res_org') is None:
        g.res_org = ResOrg()

    form = CaseForm()

    # walk thgrough the form layout and build the form fields dynamically
    for cfield in g.res_org.form_config:
        field = None
        
        if cfield['fieldtype'] == 'Text':
            field = wtf.TextField(cfield['fieldlabel'])
        elif cfield['fieldtype'] == 'TextArea':
            field = wtf.TextAreaField(cfield['fieldlabel'], 
                                      widget=TextArea(rows=cfield.get('rows', 20), 
                                                      cols=cfield.get('cols', 80)))

        elif cfield['fieldtype'] == 'Select':
            selections = get_selections(cfield['choosefrom'])
            field = wtf.SelectField(cfield['fieldlabel'], choices=selections)

        elif cfield['fieldtype'] == 'MultiSelect':
            selections = get_selections(cfield['choosefrom'])
            field = wtf.SelectMultipleField(cfield['fieldlabel'], choices=selections)
        elif cfield['fieldtype'] == "Date":
            #Need to specify a widget to allow for selecting from calendar
            field = wtf.DateField(cfield['fieldlabel'], widget=DatePickerWidget()) 
        elif cfield['fieldtype'] == "DateTime":
            #Need to specify a widget to allow for selecting from calendar
            field = wtf.DateTimeField(cfield['fieldlabel'], widget=DateTimePickerWidget()) 
        elif cfield['fieldtype'] == "Boolean":
            field = wtf.BooleanField(cfield['fieldlabel'])
        elif cfield['fieldtype'] == "Number":
            field = wtf.IntegerField(cfield['fieldlabel'])
        else:
            continue  # we don't know what you specified, so just skip it

        if field is not None:
            # Append the field to the object
            CaseForm.append_field(cfield['fieldname'], field)

    return form


# Build the list of select values from the Resilient system configuration
def get_selections(resfield):
    """
    build the list of selections
    """
    enums = g.res_org.get_enums()

    fenum = enums.get(resfield, None)
    if fenum is not None:
        choices = []
        for enum in fenum:
            for key, value in enum.iteritems():
                nselection = convert_selection(key, value)
                choices.append(nselection)
        return choices
    else:
        raise Exception

# Swap the key and value pair to a tuple of Value, key so that it is
# represented in select and multi select fields
def convert_selection(key, value):
    """
    Swap the selection tuple to be value,key
    """
    return (value, key)

# Convert the date/time string to the time since the epoch in miliseconds
def convert_date(item):
    """
    Convert the date to time since epoch
    """
    date = datetime.datetime.strptime(item, "%Y-%m-%d %H:%M:%S")
    epoch = int(time.mktime(date.timetuple())) * 1000
    return epoch


# convert multiselect returned list to a list of the integer id's for the enumerations
# the values returned are string representation of the integer
def convert_multi_select(ilist):
    """
    Make a list of the select id's
    """ 
    values = []
    for ivalue in ilist:
        values.append(int(ivalue))
    return values

# Create incident based on form and  resapi
#  Does not do anyting about wether a field is required in resilient or not
def CreateIncident(irequest):
    """
    Function to create the incident based on the web form presented
    """
    res = g.res_org
    template = deepcopy(res.create_template)
    processedfields = []

    configs = res.form_config
    for form in irequest.form:
        # check for a null string returned
        if irequest.form[form] == "" or irequest.form[form] is None:
            continue
        celement = res.get_config(form)
        if celement is not None:
            # get mapping 
            if celement.get('fieldtype') == 'DateTime': 
                value = convert_date(irequest.form[form])
            elif celement.get('fieldtype') == 'Date':  
                # Date only fields have time of 00
                value = convert_date(irequest.form[form]+" 00:00:00")
            elif re.match(celement.get('fieldtype'), "Select"):
                value = int(irequest.form[form])
            elif re.match(celement.get('fieldtype'), "MultiSelect"):
                value = convert_multi_select(irequest.form.getlist(form))
            elif 'Boolean' in celement.get('fieldtype'):
                if irequest.form[form] == 'y':
                    value = True
                else:
                    value = False
            elif 'Number' in celement.get('fieldtype'):
                value = int(irequest.form[form])
            else:
                value = irequest.form[form]

            if 'properties' in celement.get('resapi'):
                incidentitem = celement.get('resapi').split('.')[1]
                props = template.get('properties') 
                props[incidentitem] = value
            else:
                template[celement.get('resapi')] = value

        #procelement.append(ce)  # Save the processed fields so we can check for required fields

    # we will make the discovered date the current date/time
    template['discovered_date'] = int(time.mktime(datetime.datetime.utcnow().timetuple())) * 1000


    try:
        incident = res.client.post('/incidents/?want_full_data=true', template)
        flash("Case Created {}".format(incident.get('id')))
        return(incident, None)
    except Exception as ecode:
        exceptcode = ecode
        flash("CREATION ERROR - {}".format(ecode))
        return(None, exceptcode)



