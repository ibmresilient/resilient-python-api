# finfo

The `co3` module includes a command line utility __`finfo`__ that uses
the Resilient REST API to read and display metadata about fields defined
in the Resilient application.

### Usage

To print the usage information:
```
  finfo --help
```

When run with connection information but without any command-line options,
`finfo` lists basic information about incident fields, including built-in
and custom fields.

Specify a single field name to display more detail for that field.

Options are available to list fields from Data Tables and other types; 
to list valid values for 'select'-type fields, and to list the field
definitions in CSV or JSON format.


### Configuration File

Configuration parameters for the server URLs, user credentials and so on
should be provided using a configuration file.  They can optionally also
be provided on the command-line.

If the environment variable `APP_CONFIG_FILE` is set, it defines the path
to your configuration file.  The default location for this file is
`app.config` in a directory named `.resilient` under the user's home directory.

The configuration file is a text file, with a `[resilient]` section containing:

```
[resilient]
host=resilient.example.com
port=443
email=api@example.com
password=passw0rd
org=Culture
```


## Listing information about fields

Normal usage produces a list of the fields defined in an incident.  This
includes the required fields (indicated with an asterisk), required-on-close
fields (indicated with a 'c'), and any custom fields (named `properties.*`):

```
$ finfo
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
$ finfo incident_type_ids
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
