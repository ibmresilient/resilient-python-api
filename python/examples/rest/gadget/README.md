# Gadget

The `co3` module includes a command line utility __`gadget`__ that provides
general-purpose commands to access the Resilient REST API.  The `gadget`
command line program illustrates the following:

* Connecting/authenticating to the Resilient server.
* Creating an incident given a JSON file.
* Attaching files to an incident
* POSTing/DELETEing/GETting a URL.
* Listing incidents using the Resilient query API.

This directory contains various JSON templates that can be used with `gadget`.


### Usage

To print the usage information:
```
  gadget --help
```

There are various command-line options to specify a connection to the
Resilient platform.  Additional command-line options perform basic
actions using the REST API, including the ability to list, query, create
and update incidents and other Resilient objects.


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


## Examples

The following are some example usages.

List all incidents to which the user has visibility:

```
$ gadget --list
```

List all incidents matching the query in the file `name_query.json` (see [name_query.json](name_query.json) for details):

```
$ gadget --list --query name_query.json
```

Create an incident using the settings defined in [incident_template.json](incident_template.json):

```
$ gadget --create incident_template.json
```

Create an incident using the [incident_template.json](incident_template.json) template, and attach a file:

```
$ gadget --create incident_template.json --attach file.xls
```

POST a comment/note to incident 12345:

```
$ gadget --post /incidents/12345/comments comment.json
```

DELETE a comment/note from an incident:

```
$ gadget --delete /incidents/12345/comments/510
```

UPDATE an incident using the settings defined in [incident\_update\_template.json](incident\_update\_template.json):  
```
$ gadget --update /incidents/12345 incident_update_template.json
```

