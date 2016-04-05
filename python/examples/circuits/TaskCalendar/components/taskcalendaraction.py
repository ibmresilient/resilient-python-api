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
"""Action Module circuits component to mail out an ics calendar file for tasks"""

from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage
import os
import logging

from datetime import datetime
import tempfile
import smtplib
from smtplib import SMTP_SSL, SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

LOG = logging.getLogger(__name__)

LOG.setLevel(logging.DEBUG)  # force logging level to be DEBUG
CONFIG_DATA_SECTION = 'taskcalendar'


class Vcal(object):
    ''' For creating data for ics files '''
    def __init__(self):
        self.header = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-/resilientsystems.com/Resilient IRT
METHOD:PUBLISH
BEGIN:VEVENT
FBTYPE:BUSY
'''
        self.end = '''END:VEVENT
END:VCALENDAR
'''
        self.content = ""
        # variables to keep track of what components have been added

        self.url = False
        self.uid = False
        self.startd = False
        self.endd = False
        self.url = False
        self.location = False
        self.summary = False


    def add_start(self,startdate):
        if not self.startd:
            self.content +="DTSTART:{}\n".format(startdate)
            self.startd = True

    def add_end(self,enddate):
        if not self.endd:
            self.content += "DTEND:{}\n".format(enddate)
            self.endd = True

    def add_summary(self,summary):
        if not self.summary:
            self.content += "SUMMARY:{}\n".format(summary)
            self.summary = True

    def add_uid(self,uid):
        if not self.uid:
            self.content+= "UID:{}\n".format(uid)
            self.uid = True

    def build_event(self):
        return self.header+self.content+self.end

    def add_url(self,url):
        if not self.url:
            self.content += "URL:{}\n".format(url)
            self.url = True

    def add_location(self,location):
        if not self.location:
            self.content += "LOCATION:{}".format(location)
            self.location = True





class TaskCalendar(ResilientComponent):
    ''' for handling task calendar events from Resilient'''
    def __init__(self, opts):
        super(TaskCalendar, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})

        # The queue name can be specified in the config file, or default to 'taskcalendar'
        self.channel = "actions." + self.options.get("queue", "taskcalendar")

    def get_users(self):
        uri = "/users"
        try:
            self.users = self.rest_client().get(uri)
        except Exception as e:
            self.users = None
            return False
        return True


    @handler()
    def _calendar_invite_action(self, event, *args, **kwargs):
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

        LOG.debug("Event Name {}".format(event.name))
      
        incident = event.message["incident"]
        taskinfo = event.message["task"]

        inc_id = incident["id"]
        task_id = taskinfo['id']

        if taskinfo.get('owner_id',None) is not None:
            event = Vcal()
            event.add_uid("{}{}@resilientsystems.com".format(inc_id,task_id))
            event_date = datetime.now().strftime("%Y%m%dT%H%M%SZ")
            event.add_start(event_date)
            if taskinfo['due_date'] is not None:
                due_date = datetime.utcfromtimestamp(int(taskinfo.get('due_date')/1000)).strftime("%Y%m%dT%H%M%SZ")
                LOG.debug("Duedate is {}".format(due_date))
                event.add_end(due_date)
            else:
                LOG.warn("No Due Date, setting to current {}".format(event_date))
                event.add_end(event_date)

            event.add_summary("Task {} for Incident {} <{}>".format(task_id,inc_id,taskinfo.get('name')))

            event.add_url("https://{}/#incidents/{}?tab=tasks&task_id={}".format(self.opts.get('host'),inc_id,task_id))


            estring = event.build_event()
            LOG.debug(estring)
            tfile = tempfile.NamedTemporaryFile(dir='/tmp',suffix='.ics',delete=False) # create the file, but don't delete on close
            tfile.write(estring)
            tfile.close()


            rv = self.get_users()
            if not rv:
                LOG.error("Failed to retrieve users from Resilient")
                return
            if rv:
                # handle getting the email
                uemail = None
                for user in self.users:
                    if user.get('id') == taskinfo.get('owner_id'):
                        uemail = user.get('email')
                        LOG.debug("Task owner is {}".format(uemail))
                        yield "Failed to retrieve users from resilient"
            if uemail is not None:
                # Build the Mail 
                msg = MIMEMultipart()
                msg['Subject'] = "New task for incident {} assigned to you".format(inc_id)

                
                if self.options.get('sslrequired'):
                    LOG.info("SLS connection to mailbox required")
                    smtp = SMTP_SSL(self.options.get('smtpserver')+":"+self.options.get('smtpport'))
                elif self.options.get('tlsrequired'):
                    LOG.info("TLS connection to mailbox required")
                    smtp = SMTP(self.options.get('smtpserver')+":"+self.options.get('smtpport'))
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                else:
                    smtp = SMTP(self.options.get('smtpserver')+":"+self.options.get('smtpport'))

                if self.options.get('smtpuser',None) is not None:
                    try:
                        smtp.login(self.options.get('smtpuser'),self.options.get('smtppw'))
                    except smtplib.SMTPException:
                        smtp = SMTP_SSL(self.options.get('smtpserver')+":"+self.options.get('smtpport'))
                        smtp.login(self.options.get('smtpuser'),self.options.get('smtppw'))

                        
                msg['From'] = self.options.get('smtpfrom')

                part = MIMEBase('application',"octet-stream")
                part.set_payload(open(tfile.name,"rb").read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition','attachment; filename="{}"'.format(os.path.basename(tfile.name)))
                msg.attach(part)

                smtp.sendmail(self.options.get('smtpfrom'),uemail,msg.as_string())
                smtp.quit()
                os.remove(tfile.name) # remove the temporary file.
                LOG.info("Mail sent")

                yield "User {} emailed for task {} in incident {}".format(uemail,task_id,inc_id)
            else:
                LOG.error("Userid {} not found in the Resilient System".format(taskinfo.get('owner_id')))
                yield "Userid {} not found in the Resilient System".format(taskinfo.get('owner_id'))
        else:
            LOG.error("Task Due Date updated without owner set")
            yield "task {} for incident {} was not assigned to a user".format(taskinfo.get('name'),inc_id)

        yield "task %s updated" % taskinfo.get('name')
    # end _calendar_invite_action
