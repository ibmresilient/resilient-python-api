#!/usr/bin/env python

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

from __future__ import print_function

import json
from datetime import datetime
from calendar import timegm
import co3
import logging

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARN)


class ExampleArgumentParser(co3.ArgumentParser):
    def __init__(self):
        super(ExampleArgumentParser, self).__init__()

        self.add_argument('--list',
                          action='store_true',
                          help="Prints the list of incidents (including IDs and names).  See also --query.")

        self.add_argument('--query',
                          help="A template JSON file that contains a QueryDTO to limit and sort the results.")

        self.add_argument('--create',
                          help='Creates an incident using the specified JSON file as a template. '
                               'Note that the "discovered date" is set to the current time.  Also '
                               'note that the incident name and description are included directly '
                               'in the template file.  The JSON data of the created incident is '
                               'written to stdout.')

        self.add_argument('--attach',
                          nargs='*',
                          help='Specifies file(s) to attach when creating an incident.')

        self.add_argument('--get',
                          help="Generically get JSON at the specified URI.  The JSON data of the"
                               "result is written to stdout.")

        self.add_argument('--post',
                          nargs=2,
                          help="Generically post the specified JSON file to the specified URI.  The "
                               "JSON data of the created object is written to stdout.  The first argument"
                               "for this option is the URI to send the POST.  The second argument is "
                               "a template JSON file.")

        self.add_argument('--update',
                          nargs=2,
                          help="Update the resource at the specified URI using the specified JSON file."
                               "The JSON data of the updated object is written to stdout.  The first argument"
                               "for this option is the URI to GET, update, then PUT.  The second argument is"
                               "a JSON file that will be applied in the update.")

        self.add_argument('--delete',
                          help="Generically delete the specified URI.")


def show_incident_list(client, query_template_file_name):
    incidents = None
    if query_template_file_name:
        with open(query_template_file_name, 'r') as template_file:
            query = json.loads(template_file.read())
            # Get the list of incidents
            incidents = client.post('/incidents/query', query)
    else:
        incidents = client.get('/incidents')

    # Print the incident names
    for inc in incidents:
        print('{0}: {1}'.format(inc['id'], inc['name']))


def get_json_time(dt):
    return timegm(dt.utctimetuple()) * 1000


def create_incident(client, template_file_name, attachments):
    with open(template_file_name, 'r') as template_file:
        template = json.loads(template_file.read())

    # Discovered date, which is required (and can't really be hardcoded
    # in the template).
    template['discovered_date'] = get_json_time(datetime.utcnow())

    incident = client.post('/incidents', template)
    print('Created incident:  ')
    print(json.dumps(incident, indent=4))

    incident_id = incident['id']
    if isinstance(attachments, list) and len(attachments) > 0:
        for attachment in attachments:
            upload = client.post_attachment('/incidents/{0}/attachments'.format(incident_id), attachment)
            print('Created attachment:  ')
            print(json.dumps(upload, indent=4))


def generic_get(client, uri):
    incident = client.get(uri)

    print('Response:  ')
    print(json.dumps(incident, indent=4))


def generic_post(client, uri, template_file_name):
    with open(template_file_name, 'r') as template_file:
        template = json.loads(template_file.read())

    incident = client.post(uri, template)

    print('Response:  ')
    print(json.dumps(incident, indent=4))


def generic_update(client, uri, template_file_name):

    def update_func(json_data):
        with open(template_file_name, 'r') as template_file:
            template = json.loads(template_file.read())
            json_data.update(template)
        return json_data

    incident = client.get_put(uri, update_func)

    print('Response:  ')
    print(json.dumps(incident, indent=4))


def generic_delete(client, uri):
    print(client.delete(uri))


def main():
    parser = ExampleArgumentParser()

    co3_opts = parser.parse_args()

    # Create SimpleClient and connect
    verify = co3_opts.cafile or True

    url = "https://{0}:{1}".format(co3_opts.host, co3_opts.port)

    client = co3.SimpleClient(org_name=co3_opts.org, proxies=co3_opts.proxy, base_url=url, verify=verify)

    client.connect(co3_opts.email, co3_opts.password)

    if co3_opts.create:
        create_incident(client, co3_opts.create, co3_opts.attach)

    if co3_opts.list:
        show_incident_list(client, co3_opts.query)

    if co3_opts.get:
        generic_get(client, co3_opts.get)

    if co3_opts.post:
        generic_post(client, co3_opts.post[0], co3_opts.post[1])

    if co3_opts.update:
        generic_update(client, co3_opts.update[0], co3_opts.update[1])

    if co3_opts.delete:
        generic_delete(client, co3_opts.delete)


if __name__ == "__main__":
    main()
