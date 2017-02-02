"""
Action Module circuits component to mail out a .ics calendar file for tasks
"""

import os
import logging
from datetime import datetime
import tempfile
import traceback
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent
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
    # end __init__

    def _get_users(self):
        ''' Retrieve list of all system users from Resilient instance '''
        uri = "/users"
        try:
            self.users = self.rest_client().get(uri)
        except Exception as e:
            # Failed to get users.  Let exception fall up to framework.
            LOG.error(traceback.format_exc())
            raise
    # end _get_users

    def _get_task_owner_email(self, owner_id):
        ''' Find task owner's email address '''
        uemail = None
        for user in self.users:
            if user.get('id') == owner_id:
                LOG.debug("Task owner is %s", uemail)
                return user.get('email')

        # User not found
        return None
    # end _get_task_owner_email

    def _create_event(self, task_info, inc_id):
        ''' Create ics data from Resilient task info and save to file '''
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

        event_string =  event.build_event()

        return self._create_ics_file(event_string)
    # end _create_event

    @staticmethod
    def _create_ics_file(event_string):
        ''' Create a file containing the calendar data '''
        tfile = None
        filename = None
        try:
            # create the file, but don't delete on close
            tfile = tempfile.NamedTemporaryFile(dir='/tmp', suffix='.ics', delete=False)
            tfile.write(event_string.encode('utf-8'))
            filename = tfile.name
            tfile.close()

        except Exception as e:
            LOG.error(traceback.format_exc())
            # Intentionally letting exceptions fall through for framework to catch
            raise

        finally:
            if tfile:
                os.remove(filename)  # remove the temporary file.

        return filename
    # end _create_ics_file

    def _send_event_email(self, inc_id, ics_filename, send_to):
        ''' Construct and send email with event to task owner '''
        try:
            subject = "New task for incident %s assigned to you" % inc_id
            body = ""
            from_addr = self.options.get('smtpfrom')

            args = {"server": self.options.get('smtpserver')}
            port = self.options.get('smtpport')
            if port:
                args['port'] = port

            if self.options.get('use_ssl'):
                LOG.info("SSL connection to mailbox required")
                server = send_email.connect_smtp_ssl(self.options.get('smtpuser'),
                                                     self.options.get('smtppw'), **args)

            elif self.options.get('use_start_tls'):
                LOG.info("TLS connection to mailbox required")
                server = send_email.connect_smtp(self.options.get('smtpuser'),
                                                 self.options.get('smtppw'), **args)

            else:
                LOG.info("Using insecure SMTP connection")
                server = send_email.connect_smtp(self.options.get('smtpuser'),
                                                 self.options.get('smtppw'), **args)

            send_email.send_email(server, from_addr, send_to, subject, body, [ics_filename,])
            LOG.info("Mail sent")

        except Exception as e:
            # Let exception fall up for framework to handle
            LOG.error(traceback.format_exc())
            raise
    # end _send_event_email

    @handler("taskcalendar", "duedate_change")
    def calendar_invite_action(self, event, *args, **kwargs):
        """ The string passed to @handler must match the action name in Resilient """
        # You can extend this example by creating more handlers corresponding to
        # other actions in Resilient

        task = event.message["task"]
        incident = event.message["incident"]

        # Update list of Resilient users
        self._get_users()

        owner_id = task.get('owner_id')
        if not owner_id:
            # Task is not assigned to anyone
            LOG.info("Task Due Date updated without owner set")
            LOG.info("task %s for incident %s was not assigned to a user",
                     task.get('name'), incident["id"])
            yield "Task did not have an owner"
            return

        owner_email = self._get_task_owner_email(owner_id)
        if not owner_email:
            LOG.error("Couldn't retrieve task owner's email")
            raise Exception("Task Owner %s unknown email address" % owner_id)

        event_filename = self._create_event(task, incident["id"])

        if event_filename:
            self._send_event_email(incident["id"], event_filename, owner_email)
            yield "User %s emailed for task %s in incident %s" % (
                owner_email, task.get("id"), incident["id"])
        else:
            raise Exception("Error creating calendar ICS file")

    # end calendar_invite_action
