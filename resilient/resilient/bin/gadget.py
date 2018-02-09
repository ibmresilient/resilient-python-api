#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to exercise basic REST endpoints in the Resilient API"""

from __future__ import print_function

import resilient
import sys
import json
import logging
from datetime import datetime
from calendar import timegm


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARN)


class ExampleArgumentParser(resilient.ArgumentParser):
    def __init__(self, config_file=None):
        super(ExampleArgumentParser, self).__init__(config_file=config_file)

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

        self.add_argument('--patch',
                          nargs=2,
                          help="Patch the resource at the specified URI using the specified JSON file.  The JSON"
                               "file must be in PatchDTO format.  The JSON data of the updated object is written "
                               "to stdout.  The first argument for this option is the URI to PATCH.  The second "
                               "argument is a JSON file that will be patched (in PatchDTO format).")

        self.add_argument('--delete',
                          help="Generically delete the specified URI.")

        self.add_argument('--search',
                          help="Search using the specified JSON file (SearchExInputDTO)")


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
        print(u'{0}: {1}'.format(inc['id'], inc['name']))


def get_json_time(dt):
    return timegm(dt.utctimetuple()) * 1000


def create_incident(client, template_file_name, attachments):
    with open(template_file_name, 'r') as template_file:
        template = json.loads(template_file.read())

    # Discovered date, which is required (and can't really be hardcoded
    # in the template).
    template['discovered_date'] = get_json_time(datetime.utcnow())

    incident = client.post('/incidents', template)
    print('Created incident:  ', file=sys.stderr)
    print(json.dumps(incident, indent=4))

    incident_id = incident['id']
    if isinstance(attachments, list) and len(attachments) > 0:
        for attachment in attachments:
            upload = client.post_attachment('/incidents/{0}/attachments'.format(incident_id), attachment)
            print('Created attachment:  ', file=sys.stderr)
            print(json.dumps(upload, indent=4))


def generic_get(client, uri):
    incident = client.get(uri)

    print('Response:  ', file=sys.stderr)
    print(json.dumps(incident, indent=4))


def generic_post(client, uri, template_file_name):
    with open(template_file_name, 'r') as template_file:
        template = json.loads(template_file.read())

    incident = client.post(uri, template)

    print('Response:  ', file=sys.stderr)
    print(json.dumps(incident, indent=4))


def generic_update(client, uri, template_file_name):

    def update_func(json_data):
        with open(template_file_name, 'r') as update_file:
            template = json.loads(update_file.read())
            json_data.update(template)
    incident = client.get_put(uri, update_func)

    print('Response:  ', file=sys.stderr)
    print(json.dumps(incident, indent=4))


def generic_patch(client, uri, template_file_name):
    with open(template_file_name, 'r') as update_file:
        patch = resilient.Patch(json.loads(update_file.read()))

    response = client.patch(uri, patch)

    print('Response:  ', file=sys.stderr)
    print(json.dumps(response, indent=4))


def generic_delete(client, uri):
    print(client.delete(uri))


def generic_search(client, template_file_name):
    with open(template_file_name, 'r') as template_file:
        template = json.loads(template_file.read())
    results = client.search(template)

    print('Response:  ', file=sys.stderr)
    print(json.dumps(results, indent=4))


def main():
    parser = ExampleArgumentParser(config_file=resilient.get_config_file())
    opts = parser.parse_args()

    # Create SimpleClient for a REST connection to the Resilient services
    client = resilient.get_client(opts)

    if opts["create"]:
        create_incident(client, opts["create"], opts["attach"])

    if opts["list"]:
        show_incident_list(client, opts["query"])

    if opts["get"]:
        generic_get(client, opts["get"])

    if opts["post"]:
        generic_post(client, opts["post"][0], opts["post"][1])

    if opts["update"]:
        generic_update(client, opts["update"][0], opts["update"][1])

    if opts["patch"]:
        generic_patch(client, opts["patch"][0], opts["patch"][1])

    if opts["delete"]:
        generic_delete(client, opts["delete"])

    if opts["search"]:
        generic_search(client, opts["search"])

if __name__ == "__main__":
    main()
