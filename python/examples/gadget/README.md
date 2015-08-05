# Gadget

This directory contains a command line utility [gadget.py](gadget.py) that makes
use of the Resilient REST API (using the `SimpleClient` class from the `co3`
helper module).  The `gadget.py` command line program illustrates the following:

* Connecting/authenticating to the Resilient server.
* Creating an incident given a JSON file.
* Attaching files to an incident
* POSTing/DELETEing/GETting a URL.
* Listing incidents using the Resilient query API.

## Examples

The following are some example usages.

List all incidents to which the user has visibility:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --list
```

List all incidents matching the query in the file `name_query.json` (see [name_query.json](name_query.json) for details):

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --list --query name_query.json
```

Create an incident using the settings defined in [incident_template.json](incident_template.json):

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --create incident_template.json
```

Create an incident using the [incident_template.json](incident_template.json) template, and attach a file:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --create incident_template.json --attach file.xls
```

POST a comment/note to incident 12345:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --post /incidents/12345/comments comment.json
```

DELETE a comment/note from an incident:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --delete /incidents/12345/comments/510
```
