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

import os
import logging
from datetime import datetime
import tempfile
import smtplib
from smtplib import SMTP_SSL, SMTP
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent, ActionMessage
from lib.vcal import Vcal
import lib.send_email as send_email

LOG = logging.getLogger()
LOG.propagate = True

CONFIG_DATA_SECTION = 'taskcalendar'


class TaskCalendar(ResilientComponent):
    ''' for handling task update events from Resilient'''
    def __init__(self, opts):
        super(TaskCalendar, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})

        # The queue name can be specified in the config file, or default to 'taskcalendar'
        self.channel = "actions." + self.options.get("queue", "taskcalendar")
        self.users = None

    def get_users(self):
        ''' Retrieve list of all system users from Resilient instance '''
        uri = "/users"
        try:
            self.users = self.rest_client().get(uri)
        except Exception as e:
            self.users = None
            return False
        return True

    def create_event(self, task_info, inc_id):
        ''' Create ics data from Resilient task info '''
        event = Vcal()
        task_id = task_info['id']
        event.add_uid("{}{}@resilientsystems.com".format(inc_id, task_id))
        event_date = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        event.add_start(event_date)
        if task_info['due_date'] is not None:
            due_date = datetime.utcfromtimestamp(int(task_info.get('due_date')/1000))
            due_date = due_date.strftime("%Y%m%dT%H%M%SZ")
            LOG.debug("Duedate is %s", due_date)
            event.add_end(due_date)
        else:
            LOG.warn("No Due Date, setting to current %s", event_date)
            event.add_end(event_date)

        event.add_summary("Task %s for Incident %s <%s>" % (task_id, inc_id, task_info.get('name')))

        event.add_url("https://%s/#incidents/%s?tab=tasks&task_id=%s" %
                      (self.opts.get('host'), inc_id, task_id))

        return event

    @staticmethod
    def send_email(inc_id, smtp_options, ics_filename, send_to):
        ''' Construct and send email with event to task owner '''
        subject = "New task for incident %s assigned to you" % inc_id
        body = ""
        from_addr = smtp_options.get('smtpfrom')
        
        args = {"server": smtp_options.get('smtpserver')}
        port = smtp_options.get('smtpport')
        if port:
            args['port'] = port
            
        if smtp_options.get('use_ssl'):
            LOG.info("SSL connection to mailbox required")
            server = send_email.connect_smtp_ssl(smtp_options.get('smtpuser'),
                                                 smtp_options.get('smtppw'), **args)

        elif smtp_options.get('use_start_tls'):
            LOG.info("TLS connection to mailbox required")
            server = send_email.connect_smtp(smtp_options.get('smtpuser'),
                                             smtp_options.get('smtppw'), **args)
            
        else:
            LOG.info("Using insecure SMTP connection")
            server = send_email.connect_smtp(smtp_options.get('smtpuser'),
                                             smtp_options.get('smtppw'), **args)

        send_email.send_email(server, from_addr, send_to, subject, body, [ics_filename,])
        LOG.info("Mail sent")

    @handler()
    def _calendar_invite_action(self, event, *args, **kwargs):
        """The @handler() annotation without an event name makes this
           a default handler - for all events on this component's queue.
           This will be called with some "internal" events from Circuits,
           so you must declare the method with the generic parameters
           (event, *args, **kwargs), and ignore any messages that are not
           from the Actions module.
        """
        tfile = None
        if not isinstance(event, ActionMessage):
            # Some event we are not interested in
            return

        LOG.debug("Event Name %s", event.name)

        incident = event.message["incident"]
        taskinfo = event.message["task"]

        inc_id = incident["id"]

        if taskinfo.get('owner_id'):
            event = self.create_event(taskinfo, inc_id)

            estring = event.build_event()
            LOG.debug(estring)

            try:
                # create the file, but don't delete on close
                tfile = tempfile.NamedTemporaryFile(dir='/tmp', suffix='.ics', delete=False)
                tfile.write(estring.encode('utf-8'))
                tfile.close()

                success = self.get_users()
                if not success:
                    LOG.error("Failed to retrieve users from Resilient")
                    yield "Failed to retrieve users from resilient"
                    return

                # Find task owner
                uemail = None
                for user in self.users:
                    if user.get('id') == taskinfo.get('owner_id'):
                        uemail = user.get('email')
                        LOG.debug("Task owner is %s", uemail)

                if uemail is not None:
                    # Build the Mail
                    self.send_email(inc_id, self.options, tfile.name, uemail)
                    yield "User %s emailed for task %s in incident %s" % (
                        uemail, taskinfo.get('id'), inc_id)
                else:
                    LOG.error("Userid %s not found in the Resilient System",
                              taskinfo.get('owner_id'))
                    yield "Userid %s not found in the Resilient System" % taskinfo.get('owner_id')
            finally:
                # Intentionally letting exceptions fall through for framework to catch
                if tfile:
                    os.remove(tfile.name)  # remove the temporary file.

        else:
            LOG.error("Task Due Date updated without owner set")
            raise Exception("task %s for incident %s was not assigned to a user" % (
                taskinfo.get('name'), inc_id))

        yield "task %s updated" % taskinfo.get('name')


    # end _calendar_invite_action
