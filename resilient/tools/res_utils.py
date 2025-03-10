#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
    res-utils.py
    ----------

    This is a utility tool resilient SDK. Customers can
    1. Verify the connection to a resilient server
    2. Create/get incidents
    3. Attach files
    4. Get type information
    5. Get action information
    6. ...
"""
import resilient
import argparse
import logging
import json
import subprocess
import requests

import tempfile
import os

class ResClient(object):
    """

    """
    def __init__(self):
        self.res_client = None
        self.other_args = None

    def connect(self):
        print("----------------")
        print("Ready to connect")
        print("----------------")
        print("Read config information from app.confg ...")
        arg_parser = resilient.ArgumentParser(resilient.get_config_file()).parse_args(args=self.other_args)
        host = arg_parser.host
        email = arg_parser.email
        password = arg_parser.password
        org = arg_parser.org
        api_key_id = arg_parser.api_key_id
        api_key_secret = arg_parser.api_key_secret

        cafile = arg_parser.cafile

        verify = True
        if cafile is not None and cafile == "false":
            verify = False
        url = "https://{}:443".format(host)
        print("Connecting to {} using user:{}, and org:{}".format(url, email, org))
        print("Validate cert: {}".format(verify))

        args = {"base_url": url,
                "verify": verify,
                "org_name": org}

        self.res_client = resilient.SimpleClient(**args)

        if email is not None and password is not None:
            session = self.res_client.connect(email, password)

            if session is not None:
                user_name = session.get("user_displayname", "Not found")
                print("User display name is : {}".format(user_name))

            print("Done")
        else:
            self.res_client.set_api_key(api_key_id=api_key_id,
                                        api_key_secret=api_key_secret)

    def create_incident(self, infile):
        self.connect()
        with open(infile, "r") as infile:
            text = infile.read()
            print("Trying to post this dict as incident: {}".format(text))
            inc_dict = json.loads(text)
            self.res_client.post("/incidents", inc_dict)

    def count_incidents(self):
        self.connect()
        incidents = self.query_incidents()
        print("There are {} incidents".format(len(incidents)))

    def incident_type(self):
        self.connect()
        type_dict = self.res_client.get("/types/incident/fields")
        print("Incident type/fields: {}".format(type_dict))

    def get_actions(self):
        self.connect()
        resp = self.res_client.get("/actions")
        print("Actions: {}".format(resp))

    def query_incidents(self, max_count=None, page_size=1000, in_log=None):
        print("----------------------------")
        print("Download incidents and count")
        print("----------------------------")

        log = in_log if in_log else logging.getLogger(__name__)
        incidents = []
        url = "/incidents/query_paged?field_handle=-1&return_level=full"
        num_incidents = 0
        ret_num = 0
        done = False
        while not done:
            body = {
                "start": num_incidents,
                "length": page_size,
                "recordsTotal": page_size
            }
            ret = self.res_client.post(uri=url,
                                       payload=body)

            data = ret.get("data", [])
            ret_num = len(data)
            if ret_num > 0:
                log.debug("Downloaded {} incidents, total now {} ...".format(ret_num, ret_num + num_incidents))
                incidents.extend(data)
            else:
                #
                # No more to read.
                #
                done = True

            num_incidents = num_incidents + ret_num

            if max_count:
                if num_incidents >= max_count:
                    #
                    # Reach max_count set by user, stop now
                    #
                    done = True

        return incidents

    def attach_to_incident(self, filename, inc_id):
        print("-----------------------------------------")
        print("Attaching file {} to incident {}".format(filename, inc_id))
        print("-----------------------------------------")
        self.connect()

        basename = os.path.basename(filename)
        attachment_uri = "/incidents/{0}/attachments".format(inc_id)
        new_attachment = self.res_client.post_attachment(attachment_uri, filename,
                                                         filename=basename)
        print(new_attachment)

    def attach_to_incident_artifact(self, filename, inc_id, type):
        print("-----------------------------------------")
        print("Attaching file {} to incident {} as an artifact (type {})".format(filename, inc_id, type))
        print("-----------------------------------------")
        self.connect()

        basename = os.path.basename(filename)
        attachment_uri = "/incidents/{0}/artifacts/files".format(inc_id)

        new_attachment = self.res_client.post_artifact_file(uri=attachment_uri,
                                                            artifact_type=int(type),
                                                            artifact_filepath=filename,
                                                            description="Description",
                                                            value=basename)
        print(new_attachment)

def check_connect():
    """
    Use openssl and python requests to check the connection with Resilient
    :return:
    """
    arg_parser = resilient.ArgumentParser(resilient.get_config_file())
    host = arg_parser.getopt("resilient", "host")
    #
    # Use Openssl first
    #
    print("-------------------------------------")
    print("Using openssl to connect to resilient")
    print("-------------------------------------")
    command = "openssl s_client -connect {}:443".format(host)
    user = arg_parser.getopt("resilient", "email")
    password = arg_parser.getopt("resilient", "password")
    process = subprocess.Popen("/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = process.communicate(command)
    cafile = arg_parser.getopt("resilient", "cafile")
    verify = True
    if cafile is not None and cafile == "false":
        verify = False
    print(out)
    if err is not None:
        print(err)

    print("---------------------------------------------")
    print("Using python requests to connect to resilient")
    print("---------------------------------------------")

    rest_url = "https://{}:443/rest/session".format(host)
    data = '{"email": "' + user + '","password":"' + password + '", "interactive": true}'
    try:
        header = {"Content-Type": "application/json"}
        resp = requests.post(rest_url,
                             data=data,
                             headers=header,
                             verify=verify)
        print("\tResponse: " + str(resp))

    except Exception as e:
        print("\tConnection failed!!")
        print("\t" + str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="resilient SDK utility tool")

    subparsers = parser.add_subparsers(title="subcommands",
                                       help="one of these subcommands must be provided",
                                       description="valid subcommands",
                                       dest="cmd")
    subparsers.required = True

    conn_parser = subparsers.add_parser("connect",
                                        help="Make a connection")

    count_parser = subparsers.add_parser("count",
                                         help="Count incidents")

    create_parser = subparsers.add_parser("create",
                                          help="Create a new incident")

    create_parser.add_argument("-i", "--input",
                               help="file with json dict for creating a new incident",
                               required=True)

    incident_type_parser = subparsers.add_parser("incident_type",
                                                 help="Get incident type")

    check_connect_parser = subparsers.add_parser("check_connect",
                                                 help="Check connect using openssl/requests/sdk")

    get_actions_parser = subparsers.add_parser("get_actions",
                                               help="List actions")

    # attach file to incident
    attach_parser = subparsers.add_parser("attach",
                                          help="Attach a file to an incident")
    attach_parser.add_argument("-f", "--file",
                               help="file name of file to attach")
    attach_parser.add_argument("-i", "--incident",
                               help="incident id")

    # attach file to incident
    attach_artifact_parser = subparsers.add_parser("attach_artifact",
                                                   help="Attach a file to an incident as an artifact")
    attach_artifact_parser.add_argument("-f", "--file",
                                        help="file name of file to attach")
    attach_artifact_parser.add_argument("-i", "--incident",
                                        help="incident id")
    attach_artifact_parser.add_argument("-t", "--type",
                                        help="artifact type")

    args, unknown_args = parser.parse_known_args()

    res_client = ResClient()
    res_client.other_args = unknown_args

    if args.cmd == "connect":
        res_client.connect()
    elif args.cmd == "count":
        res_client.count_incidents()
    elif args.cmd == "create":
        infile = args.input
        res_client.create_incident(infile)
    elif args.cmd == "incident_type":
        res_client.incident_type()
    elif args.cmd == "check_connect":
        check_connect()
        res_client.connect()
    elif args.cmd == "get_actions":
        res_client.connect()
        res_client.get_actions()
    elif args.cmd == "attach":
        filename = args.file
        inc_id = args.incident
        res_client.attach_to_incident(filename, inc_id)
    elif args.cmd == "attach_artifact":
        filename = args.file
        inc_id = args.incident
        type = args.type
        res_client.attach_to_incident_artifact(filename, inc_id, type)


