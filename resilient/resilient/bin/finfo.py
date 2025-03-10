#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to access schema metadata with the Resilient REST API"""

from __future__ import print_function
import resilient
import json
import sys
import codecs
import csv
import collections
import logging

if sys.version_info.major < 3:
    from StringIO import StringIO
else:
    from io import StringIO


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARN)
LOG = logging.getLogger(__name__)


def wrap_io(stream):
    """Wrap the stream to always always output in utf-8"""
    if stream.encoding != 'UTF-8':
        if sys.version_info.major < 3:
            return codecs.getwriter('utf-8')(stream, 'strict')
        else:
            return codecs.getwriter('utf-8')(stream.buffer, 'strict')
    return stream

# Always always output in utf-8
sys.stdout = wrap_io(sys.stdout)
sys.stderr = wrap_io(sys.stderr)


class FinfoArgumentParser(resilient.ArgumentParser):
    def __init__(self, config_file=None):
        super(FinfoArgumentParser, self).__init__(config_file=config_file)

        self.add_argument('fieldname',
                          nargs="?",
                          help="The field name.")

        self.add_argument('--types',
                          action='store_true',
                          help="Print the list of types.")

        self.add_argument('--type',
                          dest="field_type",
                          default="incident",
                          help="The object type.  This can be the API Access Name of a "
                               "Data Table, or one of the standard types: 'incident' "
                               "(the default), 'task', 'artifact', 'milestone', "
                               "'attachment', 'note', or 'actioninvocation'.")

        self.add_argument('--json',
                          action='store_true',
                          help="Print the field definition in JSON format.")

        self.add_argument('--csv',
                          action='store_true',
                          help="Print the field lists in CSV format.")

        self.add_argument('--values',
                          dest="field_values",
                          action='store_true',
                          help="Print the list of valid values for all fields.")


def apiname(field):
    """The full (qualified) programmatic name of a field"""
    if field["prefix"]:
        fieldname = u"{}.{}".format(field["prefix"], field["name"])
    else:
        fieldname = field["name"]
    return fieldname


def print_json(field):
    """Print the definition of one field, in JSON"""
    print(json.dumps(field, indent=4))


def print_details(field):
    """Print the definition of one field, in readable text"""
    print(u"Name:        {}".format(apiname(field)))
    print(u"Label:       {}".format(field["text"]))
    print(u"ID:          {}".format(field["id"]))
    print(u"Type:        {}".format(field["input_type"]))
    if "tooltip" in field:
        if field["tooltip"]:
            print(u"Tooltip:     {}".format(field["tooltip"]))
    if "placeholder" in field:
        if field["placeholder"]:
            print(u"Placeholder: {}".format(field["placeholder"]))
    if "required" in field:
        print(u"Required:    {}".format(field["required"]))
    if "values" in field:
        if field["values"]:
            print("Values:")
            v = sorted(field["values"], key=lambda x: x["value"])
            for value in v:
                default_flag = " "
                if value["default"]:
                    default_flag = "*"
                if not value["enabled"]:
                    default_flag = "x"
                label = value["label"]
                print (u'{} {}={}'.format(default_flag, value["value"], label))


def find_field(client, fieldname, objecttype="incident"):
    trimname = fieldname[fieldname.rfind(".")+1:]
    t = client.get("/types/{}/fields".format(objecttype))
    for field in t:
        if field["name"] == trimname:
            return field


def list_fields_csv(client, objecttype="incident"):
    """Print a list of fields, in CSV format"""
    iostr = StringIO()
    writer = None
    t = client.get("/types/{}/fields".format(objecttype))
    for field in sorted(t, key=apiname):
        columns = collections.OrderedDict()
        columns["name"] = apiname(field)
        columns["required"] = field.get("required", "")
        columns["input_type"] = field.get("input_type", "")

        if sys.version_info.major < 3:
            columns["text"] = field.get("text", "").encode("utf-8")
            columns["tooltip"] = field.get("tooltip", "").encode("utf-8")
            columns["placeholder"] = field.get("placeholder", "").encode("utf-8")
        else:
            columns["text"] = field.get("text", "")
            columns["tooltip"] = field.get("tooltip", "")
            columns["placeholder"] = field.get("placeholder", "")

        if not writer:
            writer = csv.DictWriter(iostr, fieldnames=columns.keys(), dialect='excel')
            writer.writeheader()
        writer.writerow(columns)

    result = iostr.getvalue()
    if sys.version_info.major < 3:
        print(result.decode("utf-8"))
    else:
        print(result)


def list_fields_values(client, objecttype="incident"):
    """Print a list of fields' valid values, in CSV format"""
    LOG.info("values")
    iostr = StringIO()
    writer = None
    t = client.get("/types/{}/fields".format(objecttype))
    for field in sorted(t, key=apiname):
        if field.get("input_type", "") not in ["multiselect_members", "select_owner"]:
            if "values" in field:
                if field["values"]:
                    v = sorted(field["values"], key=lambda x: x["value"])
                    for value in v:
                        e = ""
                        if not value["enabled"]:
                            e = "False"
                        columns = collections.OrderedDict()
                        columns["name"] = apiname(field)
                        columns["enabled"] = e
                        columns["value"] = value["value"]

                        if sys.version_info.major < 3:
                            columns["default"] = str(value["default"] or "").encode("utf-8")
                            columns["label"] = (value["label"] or "").encode("utf-8")
                        else:
                            columns["default"] = str(value["default"] or "")
                            columns["label"] = str(value["label"] or "")

                        if not writer:
                            writer = csv.DictWriter(iostr, fieldnames=columns.keys(), dialect='excel')
                            writer.writeheader()
                        writer.writerow(columns)

    result = iostr.getvalue()
    if sys.version_info.major < 3:
        print(result.decode("utf-8"))
    else:
        print(result)


def list_fields(client, objecttype="incident"):
    """Print a list of fields, in readable text"""
    print("Fields:")
    t = client.get("/types/{}/fields".format(objecttype))
    for field in sorted(t, key=apiname):
        required_flag = " "
        if "required" in field:
            if field["required"] == "always":
                required_flag = "*"
            if field["required"] == "close":
                required_flag = "c"
        print(u"{} {}".format(required_flag, apiname(field)))


def list_types(client):
    """Print a list of types, in readable text"""
    print("Types:")
    t = client.get("/types")

    def print_types(parent, indent):
        if indent > 10:
            return
        for type in sorted(t.keys()):
            typedef = t[type]
            typename = typedef["display_name"]
            parents = typedef["parent_types"]
            if (parent is None and len(parents) == 0) or (parent in parents):
                print(u"{}{}".format(' ' * indent, type))
                print_types(type, indent+2)

    print_types(None, 2)


def main():
    """Main"""
    # Parse commandline arguments
    parser = FinfoArgumentParser(config_file=resilient.get_config_file())
    opts = parser.parse_args()

    # Connect to Resilient
    client = resilient.get_client(opts)

    # If no field is specified, list them all
    if not opts.fieldname:
        if opts.types:
            list_types(client)
        elif opts.field_values:
            list_fields_values(client, opts.field_type)
        elif opts.csv:
            list_fields_csv(client, opts.field_type)
        else:
            list_fields(client, opts.field_type)
        exit(0)

    # Find the field and display its properties
    field_data = find_field(client, opts.fieldname, opts.field_type)
    if field_data:
        if opts.json:
            print_json(field_data)
        else:
            print_details(field_data)
        exit(0)
    else:
        print(u"Field '{}' was not found.".format(opts.fieldname))
        exit(1)


if __name__ == "__main__":
    main()
