# finfo

This directory contains a command line utility [finfo.py](finfo.py) that uses
the Resilient REST API (using the `SimpleClient` class from the `co3` module)
do read and display metadata about fields defined in the Resilient application.

### Usage

To print the usage information:
```
  python finfo.py --help
```
Required parameters include the Resilient host name, and user email to
access the server.  Optional parameters include the organization name,
if the user is member of multiple organizations.

## Listing information about fields

Normal usage produces a list of the fields defined in an incident.  This
includes the required fields (incidated with an asterisk), required-on-close
fields (indicated with a 'c'), and any custom fields (named `properties.*`):

```
$ python finfo.py --email user@mycompany.com --host co3 --cafile cacerts.pem
Fields:
  addr
  city
  confirmed
  country
  create_date
  crimestatus_id
  description
* discovered_date
  (etc.)
```
Add the `--csv` option to produce a more detailed report in CSV format.

Use the `--type` option to see the fields for the other datatypes (task,
artifact, milestone, and so on).

## Listing information about a field

If you specify the name of a field, the utility reports information about
the definition of the field, such as its datatype and label.  For `select`
and `multiselect` fields, it also lists the label and ID of the valid values.

```
$ python finfo.py --email user@mycompany.com --host co3 --cafile cacerts.pem incident_type_ids
Name:        incident_type_ids
Label:       Incident Type
Type:        multiselect
Tooltip:     The type of incident
Placeholder: Choose Some Types
Values:
  1=Lost PDA / smartphone
  3=Lost PC / laptop / tablet
  4=Lost documents / files / records
  6=Improper disposal: digital asset(s)
  7=Improper disposal: documents / files
  (etc.)
```
