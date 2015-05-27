# Python Examples (python directory)

This directory contains the Co3 Python client librari (co3 subdirectory) and examples for the CAF and REST APIs (examples subdirectory)

## Certificates
Note that in order to connect to the server, you must provide the server's
CA certificate in a file (e.g. "cacerts.pem").  The quickest way to do this
is to use either openssl or the Java keytool command line utilities.

Using openssl to create the cacerts.pem file (using Linux or Mac OS):
```
openssl s_client -connect SERVER:65001 -showcerts -tls1 < /dev/null > cacerts.pem 2> /dev/null
```
Using keytool to create the cacerts.pem file (Linux, Mac OS or Windows):
```
keytool -printcert -rfc -sslserver SERVER:65001 > cacerts.pem
```
WARNING:  In a production setting, you will definitely want to get the certificate from a trusted source and confirm its fingerprint.

The host you specify with `--host` must match exactly the name in the server certificate.  If there is a mismatch, the permanent solution is to either change your DNS server or change the server certificate so it matches.  It is also possible to modify your hosts file temporarily, but that is not a permanent solution.

## Co3 Python Client (python/co3 directory)

The Co3 Python Client (co3 module) is a simple wrapper around the Python requests module that contains tools helpful in calling the Co3 REST API and Custom Action Framework (CAF).

It provides a SimpleClient class that you use to call the Co3 REST API.

It provides an ArgumentParser class (which extends argparse.ArgumentParser) to simplify the writing of command line utilities.  It provides support for arguments such as --host and --email that Co3-oriented command line tools will generally need.

To install this module, run these commands:
```
$ python setup.py build
$ sudo python setup.py install
```
Note that if you are using Python 3, then use `python3` instead of `python`.

## Co3 REST API Examples (python/examples/rest directory)

This directory contains a command line utility (gadget.py) that makes use of the Co3 REST API (using the co3.SimpleClient class mentioned above).  The gadget.py command line program illustrates the following:

* Connecting/authenticating to the Co3 server.
* Creating an incident given a JSON file.
* POSTing/DELETEing/GETting a URL
* Listing incidents using the Co3 query API.

The following are some example usages.

Lists all incidents to which the user has visibility:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --list
```

Lists all incidents matching the query in the file name_query.json (see name_query.json for details):

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --list --query name_query.json
```

Creates an incident using the settings defined in incident_template.json:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --create incident_template.json
```

POST a comment/note to incident 12345:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --post /incidents/12345/comments comment.json
```

DELETE a comment/note from an incident:

```
$ python gadget.py --email user@mycompany.com --host co3 --cafile cacerts.pem --delete /incidents/12345/comments/510
```

## CAF Examples (python/examples/caf directory)

This directory contains example CAF processors written in Python.  It assumes have installed the co3 module (see `/python/co3/README` for instructions on how to install the co3 module).

These scripts were written to support either Python 2 or 3.  Python 3 has better TLS certificate validation built in and is recommended for new applications.

## basic.py

The basic.py script does the following:

  * Connects to the Co3 server on port 65001 using the STOMP protocol
  * Illustrates the correct way to validate the server certificate
  * Waits for messages on the specified message destination
  * When a message is received, it displays the incident ID, name and severity text.
  * Illustrates how you can use the message's metadata to convert ID values to text.
  * Shows how to reply/acknowledge the message (so that a message appears in the Co3 Action Status page).

You start the processor from the command line.  To print the usage, do this:

```
  python basic.py --help
```

The following is an example usage.  In this example, we are connecting to a host named co3.xyz.com using a user name of user@xyz.com.  The message destination's programmatic name is "test" and the organization ID is 201.  The cacerts.pem file contains the trusted CA certificates.  You will be prompted to enter your password.

```
  $ python basic.py --cafile cacerts.pem --host co3.xyz.com --email user@xyz.com actions.201.test
```

## advanced.py

The `advanced.py` script is similar to `basic.py`, but it also shows how you can connect back to the Co3 server with the Co3 REST API.  In this example, it simply updates the incident description to include the time.

It is worth noting that when updating an incident, you must consider the possibility that another user has updated the incident.  This script handles that by using the SimpleClient.get_put method, which accepts a function that applies the changes to the incident.  The get_put method does a get, calls the apply function then performs the put.  If the put fails with a 409 Conflict error, then the get/apply/put is tried again.

You start the processor from the command line.  To print the usage, do this:

```
  python advanced.py --help
```

The usage is identical to the basic.py script, except that since it connects to the Co3 server using the REST API, you may need to specify the `--org` option (if your user is in multiple Co3 organizations).
