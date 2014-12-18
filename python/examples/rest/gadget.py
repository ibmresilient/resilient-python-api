#!/usr/bin/env python

# Co3 Systems, Inc. ("Co3") is willing to license software or access to 
# software to the company or entity that will be using or accessing the 
# software and documentation and that you represent as an employee or 
# authorized agent ("you" or "your" only on the condition that you 
# accept all of the terms of this license agreement.
#
# The software and documentation within Co3's Development Kit are 
# copyrighted by and contain confidential information of Co3. By 
# accessing and/or using this software and documentation, you agree 
# that while you may make derivative works of them, you:
#
# 1)   will not use the software and documentation or any derivative 
#      works for anything but your internal business purposes in 
#      conjunction your licensed used of Co3's software, nor
# 2)   provide or disclose the software and documentation or any 
#      derivative works to any third party.
# 
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
# OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import getopt
import getpass
import json
from datetime import datetime
from calendar import timegm
import co3

class ExampleArgumentParser(co3.ArgumentParser):
    def __init__(self):
        super(ExampleArgumentParser, self).__init__()

        self.add_argument('--list', 
            action = 'store_true',
            help = "Prints the list of incidents (including IDs and names).  See also --query.")

        self.add_argument('--query',
            help = "A template JSON file that contains a QueryDTO to limit and sort the results.")

        self.add_argument('--create',
            help = 'Creates an incident using the specified JSON file as a template. '
                   'Note that the "discovered date" is set to the current time.  Also '
                   'note that the incident name and description are included directly '
                   'in the template file.  The JSON data of the created incident is '
                   'written to stdout.')

        self.add_argument('--post',
            nargs = 2,
            help = "Generically post the specified JSON file to the specified URI.  The "
                   "JSON data of the created object is written to stdout.  The first argument" 
                   "for this option is the URI to send the POST.  The second argument is "
                   "a template JSON file.")

        self.add_argument('--delete',
            help = "Generically delete the specified URI.")

def show_incident_list(client, query_template_file_name):
    incidents = None
    if query_template_file_name:
        file = open(query_template_file_name, 'r')

        query = json.loads(file.read())

        # Get the list of incidents 
        incidents = client.post('/incidents/query', query)
    else:
        incidents = client.get('/incidents')

    # Print the incident names
    for inc in incidents:
        print('{}: {}'.format(inc['id'], inc['name']))

def get_json_time(dt):
    return timegm(dt.utctimetuple()) * 1000

def create_incident(client, template_file_name):
    file = open(template_file_name, 'r')

    template = json.loads(file.read())

    # Discovered date, which is required (and can't really be hardcoded 
    # in the template).
    template['discovered_date'] = get_json_time(datetime.utcnow())

    incident = client.post('/incidents', template)

    print('Created incident:  ')
    print(json.dumps(incident, indent=4))

def generic_post(client, uri, template_file_name):
    file = open(template_file_name, 'r')

    template = json.loads(file.read())

    incident = client.post(uri, template)

    print('Response:  ')
    print(json.dumps(incident, indent=4))

def generic_delete(client, uri):
    print(client.delete(uri))

def main(argv):
    parser = ExampleArgumentParser()

    co3_opts = parser.parse_args()

    # Create SimpleClient and connect
    verify = True
    if co3_opts.cafile:
        verify = co3_opts.cafile

    url = "https://{}:{}".format(co3_opts.host, co3_opts.port)
    
    client = co3.SimpleClient(org_name=co3_opts.org, proxies=co3_opts.proxy, base_url=url, verify=verify)

    client.connect(co3_opts.email, co3_opts.password)
 
    if co3_opts.create:
        create_incident(client, co3_opts.create)

    if co3_opts.list: 
        show_incident_list(client, co3_opts.query)

    if co3_opts.post:
        generic_post(client, co3_opts.post[0], co3_opts.post[1])

    if co3_opts.delete:
        generic_delete(client, co3_opts.delete)

if __name__ == "__main__":
    main(sys.argv[1:])
