# Python API Packages

This directory contains

 * [co3](co3), the Resilient Python Client Module for the Resilient APIs,
 * [resilient_circuits](resilient-circuits), an application framework for Action Module,
 * [pytest_resilient_circuits](pytest-resilient-circuits), a collection of pytest fixtures, 
 * and [examples](examples) for the Resilient REST API and Resilient Action Module.


## Python Client Module

The Resilient Python Client (`co3` module) contains tools helpful in calling
the Resilient REST API and Action Module.

It provides a SimpleClient class that you use to call the Resilient REST API.
This class manages an authenticated connection to the Resilient server, and
provides simple helper methods for accessing REST resources.

The module also provides an ArgumentParser (which extends `argparse.ArgumentParser`)
to simplify the writing of command line utilities.  This provides support for
standard arguments such as `--host` and `--email` that Resilient-oriented
command line tools will generally need.  The ArgumentParser can read defaults
from a configuration file, and override them from the command line.


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

__Configuration Values From Keystore__  
   Values in the config file can be pulled from a compatible keystore system
   on your OS.  To retrieve a value from a keystore, set it to ^\<key\>  
   
Example from app.confg:  
```
[resilient]
password=^resilient_password
```

__Adding the Values to Keystore__  
  The co3 package includes a utility to add all of the keystore-based values from 
  your app.config file to your system's compatible  keystore system.  Once you have 
  created the keys in your app.config file, run `res-keyring` and you will be 
  prompted to create the secure values to store.  
  
  ```
  bash-3.2$ res-keyring 
  Configuration file: /Users/kchurch/.resilient/app.config
  Secrets are stored with 'keyring.backends.OS_X'
  [resilient] password: <not set>
  Enter new value (or <ENTER> to leave unchanged): 
  ```
  
__Configuration Values From Environment__  
  Values in your config file can also be pulled from environment variables.
  To retrieve a value from the environment, set it to $\<key\>  

Example from app.confg:  
```
[resilient]
password=$resilient_password
```

A standard way to initialize a SimpleClient with this configuration is,

```
# Read the standard Resilient APIs configuration file
# - default location is ~/.resilient/app.config
# - or the location set in $APP_CONFIG_FILE
# and any other arguments specified on the command line
parser = co3.ArgumentParser(config_file=co3.get_config_file())
opts = parser.parse_args()

# Initialize a SimpleClient with these options
client = co3.get_client(opts)

```

### Installing the 'co3' module

Current versions of the release package are available on GitHub:
https://github.ibm.com/Resilient/resilient-api/releases


Install the package file using `pip`:

    pip install co3-x.x.x.tar.gz

(the filename will vary according to the current version).

You can build release package files locally, by

    bash ./buildall.sh <version_number>

where <version_number> is a build number (1, 2, etc).


## Action Module Application Framework

The Resilient-Circuits Application Framework (`resilient_circuits` module)
is a very lightweight component-based framework for writing applications
that respond to Action Module events.

It provides an extensible "application" class that loads any Python files
in the application's `components` directory as well as any installed 
compatible packages. For each of these components, it automatically subscribes 
to the appropriate Action Module message destination (queue or topic), and 
dispatches messages to the relevant method.

The framework manages the connection to the Action Module, including any
reconnection after a network outage.  It also manages acknowledgement of
action messages and sending action status back to the server.

To develop a component, you simply subclass the `ResilientComponent` class.
This superclass includes several utility functions that provide convenient
access to the REST API and action message data.

Examples can be found [examples/action-modules](here).

### Installing the 'resilient_circuits' module

Current versions of the release package are available on GitHub:
https://github.ibm.com/Resilient/resilient-api/releases

Install the package file using `pip`:

    pip install resilient_circuits-x.x.x.tar.gz

(the filename will vary according to the current version of this repository).


## Certificates

Note that in order to connect to the Resilient server, if the server
doesn't have a trusted TLS certificate, you must provide the server's
certificate in a file (e.g. "cacerts.pem").  The quickest way to do this
is to use either `openssl` or the Java `keytool` command line utilities.

Using openssl to create the cacerts.pem file (using Linux or Mac OS):
```
openssl s_client -connect SERVER:443 -showcerts -tls1 < /dev/null > cacerts.pem 2> /dev/null
```

Using keytool to create the cacerts.pem file (Linux, Mac OS or Windows):
```
keytool -printcert -rfc -sslserver SERVER:443 > cacerts.pem
```

WARNING:  In a production setting, you should take care to get the certificate
from a trusted source and confirm its fingerprint.

When connecting to a Resilient server with the Python libraries,
the hostname you specify must match exactly the name in the server
certificate.  If there is a mismatch, the permanent solution is to either
change your DNS server or change the server certificate so it matches. It is
also possible to modify your hosts file temporarily, but that is not a permanent
solution.


## Resilient API Examples (python/examples directory)

The [examples](examples) directory contains several utilities and examples
that make use of the Resilient REST API and the Resilient Action Module.

For further details, see the `README.md` supplied with each example.
