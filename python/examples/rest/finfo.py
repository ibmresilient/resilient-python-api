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

import co3 as resilient
import json
import sys
import codecs
import locale
import requests

def wrap_io(stream):
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
    def __init__(self):
        super(FinfoArgumentParser, self).__init__()

        self.add_argument('fieldname',
            nargs = "?",
            help = "The field name.")

        self.add_argument('--type',
            default = "incident",
            choices = ["incident", "task", "artifact", "milestone", "attachment", "note"],
            help = "The object type (defaults to 'incident')")

        self.add_argument('--json',
            action = 'store_true',
            help = "Print the field definition in JSON format.")


def apiname(field):
    if field["prefix"]:
        fieldname = u"{}.{}".format(field["prefix"], field["name"])
    else:
        fieldname = field["name"]
    return fieldname

def print_json(field):
    print(json.dumps(field, indent=4))

def print_details(field):
    print(u"Name:        {}".format(apiname(field)))
    print(u"Label:       {}".format(field["text"]))
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
            v = sorted(field["values"], key=lambda x : x["value"])
            for value in v:
                default_flag = " "
                if value["default"]:
                    default_flag = "*"
                if not value["enabled"]:
                    default_flag = "x"
                label = value["label"]
                print (u'{} {}={}'.format(default_flag, value["value"], label))

def find_field(client, fieldname, type="incident"):
    trimname = fieldname[fieldname.rfind(".")+1:]
    t = client.get("/types/{}/fields".format(type))
    for field in t:
        if field["name"]==trimname:
            return field

def list_fields(client, type="incident"):
    print("Fields:")
    t = client.get("/types/{}/fields".format(type))
    for field in sorted(t, key=lambda x : apiname(x)):
        required_flag = " "
        if "required" in field:
            if field["required"]=="always":
                required_flag = "*"
            if field["required"]=="close":
                required_flag = "c"
        print(u"{} {}".format(required_flag, apiname(field)))

def main(argv):
    # Parse commandline arguments
    parser = FinfoArgumentParser()
    opts = parser.parse_args()

    # Create SimpleClient and connect
    verify = True
    if opts.cafile:
        verify = opts.cafile
    url = "https://{}:{}".format(opts.host, opts.port)

    # Disable all the SSL warnings from requests
    # because we're running commando, verify off
    requests.packages.urllib3.disable_warnings()
    client = resilient.SimpleClient(org_name=opts.org, proxies=opts.proxy, base_url=url, verify=False)
    client.connect(opts.email, opts.password)

    # If no field is specified, list them all
    if not opts.fieldname:
        list_fields(client, opts.type)
        exit(0)

    # Find the field and display its properties
    field_data = find_field(client, opts.fieldname, opts.type)
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
    main(sys.argv[1:])
