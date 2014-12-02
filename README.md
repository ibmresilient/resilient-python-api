# Introduction

This project contains utilities and sample code for the Co3 APIs (both the CAF and REST APIs).
The following is the top level directory structure:

 Directory  | Description
 ---------- | -----------
 dotnet     | Microsoft .NET examples, specifically a ASP.NET form that allows users to submit incidents without needing a Co3 account
 java       | Java REST API and CAF examples
 python     | Python REST API and CAF examples

# Example FAQ/Index

You may be here because you are looking for a specific example of accomplishing a task or have a specific question.  This section will attempt to get you pointed in the right direction.

## General ##

***What is the difference between the Co3 REST API and the Co3 Custom Action Framework (CAF)?***

The Co3 REST API is allows programs to get and modify data within the Co3 system.  Using this API you can create, modify, query and delete incident-oriented information.  The Co3 Web UI uses the REST UI to do everything.  You can write clients that use the REST API in the same ways.

The Co3 Custom Action Framework allows you to respond to "actions" (either manual or automatic) that the server generates.  The Custom Action Framework Programmer's Guide contains much more information about this framework.

***I need an example that I cannot find here.  Can you help?***

We love to help customers be successful!  Please contact use at success@co3sys.com.

## Python ##

***Where are the Python examples?***

The Python examples are located in the "python" subdirectory.  The following subdirectories exist within that directory:

* co3 - This directory contains a Python module that is used by all of the Python examples.  You'll probably want to install this module before continuing with the Python examples.  See the [Co3 Python Client](#co3-python-client-pythonco3-directory) section for details.
* examples/rest - Examples showing how you can use the Co3 REST API with Python.  See the [Co3 REST API Examples](#co3-rest-api-examples-pythonexamplesrest-directory) section for details.
* examples/caf - Examples showing how to use the Co3 CAF with Python.  See the [Co3 CAF Examples](#caf-examples-pythonexamplescaf-directory) section for details.

***Which version of Python do the examples use?***

They should work fine with the latest release of Python 2 or 3.  Python 3 is recommended, however, since it has better support for SSL certificate handling.

***How do I run the Python examples?***

This is discussed in the [Python](#python-examples-python-directory) section below.  

Note that your first step will likely be to install the "co3" Python module.  See the [Co3 Python Client](#co3-python-client-pythonco3-directory) section for more information.

All of the Python examples show a command line usage if you run them with the --help argument.  One key point worth calling out here is that you have to somehow tell the example programs how to determine if the server certificate is trusted.  You do this with the --cafile argument.  See the [Certificates](#certificates) sub-section for a discussion.

***Where can I find a Python example that just uses the REST API?***

There is such an example in python/examples/rest/gadget.py.  This tool is useful for exploring the REST API because it allows you to generally GET/PUT/POST/DELETE to the Co3 server.  See the [Co3 REST API Examples](#co3-rest-api-examples-pythonexamplesrest-directory) section for more information.

***Where can I find a very basic Python CAF example?***

There is a basic Python CAF example in python/examples/caf/basic.py.  This example implements a command line interface that allows you to watch a queue/topic.  It simply prints to the console when a message is received.  It also replies to the server with a "Processing complete" completion message.

See the [basic.py](#basicpy) section for more information.

***Where can I find a Python CAF example that connects back to the Co3 server using the REST API?***

There is such an example in python/examples/caf/advanced.py.  This example builds on basic.py (mentioned above).  It connects back to the Co3 server to append to the incident's description.  

See the [advanced.py](#advancedpy) section for more information.

## Java ##

***Where are the Java examples?***

The Java examples are in the "java" directory.  The following subdirectories exist within that directory:

* examples/caf/general - Groovy examples that read CAF actions from a destination and invoke Co3 REST API commands.  See the [Co3 CAF General Examples](#co3-caf-general-examples-javaexamplescafgeneral) section for details.
* examples/caf/camel - Apache Camel example that reads CAF actions from a destination and adjusts the incident severity based on the incident type.  See the [Apache Camel Example](#apache-camel-example-javaexamplescafcamel-directory) section for details.
* examples/caf/mulesoft - Mulesoft Anypoint Studio example that illustrates how to read from a message destination and post to HipChat; see the [Mulesoft HipChat Example](#mulesoft-hipchat-example-javaexamplescafmulesofthipchat-directory) section for details.  Note that you will need to install Mulesoft Anypoint Studio to use this example.
* examples/rest - A collection of examples that illustrate various ways to use the Co3 REST API.  See the [Co3 REST API Examples](#co3-rest-api-examples-javaexamplesrest-directory) section for details.
* jms-util - A library that allows for secure connections to Apache ActiveMQ servers.  See the [Co3 JMS Utilities](#co3-jms-utilities-javajms-util-directory) section for details.  All of the CAF examples use this library because the default Active MQ client library does not check for certificate common name mismatch errors.

***What Java version do the examples use?***

The examples were written using Java 7, although you should be able to run them with Java 6 - 8.

Some of the examples are written in Groovy v2.3.6.

***How do you build the examples?***

We use Gradle to build the examples.  See the [Java Examples](#java-examples-java-directory) section below for more information.

***What's the best way to explore the Java examples?***

We highly recommend that you use Eclipse for this.  You will need to have the Gradle Eclipse add-in installed.  Once you have done that, you can import the Gradle project in the "java" directory.

***What is Mulesoft?***

Mulesoft is an Enterprise Service Bus (ESB) that allows you to run multiple integrations (Co3-related or not) within a single environment.  An ESB can be helpful if you have many different systems that need to interact with one anohter.  If you already have an ESB, you may want to consider having your Co3 integrations run within it.

The Mulesoft ESB also has a number of pre-built connectors that might simplify integrations with Co3.

See https://www.mulesoft.org for more information on Mulesoft.

See the [Mulesoft HipChat Example](#mulesoft-hipchat-example-javaexamplescafmulesofthipchat-directory) section for an example of how you can use Mulesoft to integrate Co3 with a chat client (HipChat in our example).

If you do not need to full power of an ESB such as Mulesoft, you may wish to consider a lighter-weight alternative such as Apache Camel (see below).

***What is Apache Camel?***

Camel allows you to create "routes" that describe how messages (such as CAF messages) get processed.  Apache Camel is an open source tool with built-in connectors that may help simplify integrations with Co3.

See the [Apache Camel Example](#apache-camel-example-javaexamplescafcamel-directory) section for an example of how you can use Camel to integrate with Co3.

# Java Examples (java directory)

The Java examples can be built using the Gradle build system (see http://www.gradle.org).  To build them, you simply cd into the java directory and type:

  $ gradle build

However, it is generally more useful to see the examples from within an IDE.  You can import the Gradle project into Eclipse if you have the Gradle Integration for Eclipse installed.  It also assumes that you have Groovy support installed into Eclipse.

## Co3 REST API Examples (java/examples/rest directory)

This project contains sample command line utilities that use the Co3 REST API (and SimpleClient class).

The output from the Gradle build is a "One JAR" file (http://one-jar.sourceforge.net) that can easily be run from the command line.

You can also run and debug the examples directly from within Eclipse.  This assumes some level of familiarity with Eclipse, but debugging the examples can help quickly understand what's happening.

The following are some examples of running the examples using the One JAR file from the command line.

### Running IncidentUtil

The IncidentUtil class is the default "main class" for the co3-rest-examples.jar file, so you can invoke it from the command line using the following command:

```
$ java -jar build/libs/co3-rest-examples.jar -h
```

### Running InviteUsers

To run InviteUsers from the command line, you need to override the default "main class" like this:

```
$ java -Done-jar.main.class=com.co3.examples.InviteUsers -jar build/libs/co3-rest-examples.jar -h
```

## Co3 JMS Utilities (java/jms-util directory)

The current version of the ActiveMQ client library (5.10.0) does no validate that the host name you think you're connecting to is actually what is in the certificate commonName or subjectAltName (see https://issues.apache.org/jira/browse/AMQ-5443 for details).

To workaround this issue, Co3 has provided a Co3ActiveMQSslConnectionFactory class that checks the host name.  Using this Co3ActiveMQSslConnectionFactory directly in Java code is relatively straightforward:

```
Co3ActiveMQSslConnectionFactory factory = new Co3ActiveMQSslConnectionFactory("ssl://co3:65000");

factory.setUserName("user@mycompany.com");
factory.setPassword("userpassword");
factory.setTrustStore("keystore");
factory.setTrustStorePassword("password");

Connection con = factory.createConnection();

...

```

There is an example of how this would translate to Mulesoft/Spring in the java/examples/caf/mulesoft/hipchat directory.

In general, when connecting to a the Co3 server using JMS you should use the Co3ActiveMQSslConnectionFactory class to avoid man-in-the-middle vulnerabilities.  That is, unless you have some other way to ensure the integrity of the SSL connection.

## Co3 CAF General Examples (java/examples/caf/general)

This project contains example Groovy code to interact with message destinations.  The following table describes each example Groovy class in detail:

Class Name           | Description
-------------------- | -----------
DestinationWatcher   | A helper class that simplifies connecting to and reading from message destinations.
WatchDestination     | A command line tool that uses DestinationWatcher.  This can be used to test that messages are being sent to a destination.
LookupUsername       | A command line tool that watches a destination for "user name" artifact changes and updates them using the Co3 REST API.

See the comments in each of the Groovy classes for more information.

The output from the Gradle build is a "One JAR" file (http://one-jar.sourceforge.net) that can easily be run from the command line.

You can also run and debug the examples directly from within Eclipse.  This assumes some level of familiarity with Eclipse, but debugging the examples can help quickly understand what's happening.

The following illustrates how you can run the command line utilities from the command shell.

### Running WatchDestination
The WatchDestination class is the default "main class" for the co3-caf-examples.jar file, so you can invoke it from the command line using the following command:

```
$ java -jar build/libs/co3-caf-examples.jar -h
```

To connect to a destination with a full name of "actions.201.mydest", you'd do something like this:

```
$ java -jar build/libs/co3-caf-examples.jar -server co3 -truststore keystore -truststorepassword password -user user@mycompany.com actions.201.test
Password: <ENTER PASSWORD HERE>
```

### Running LookupUsername
In order to run LookupUsername, you must first copy the config.json.dist file to config.json, then edit the settings in your new config.json file.

The LookupUsername is not the default "main class" for the co3-caf-examples.jar file, so you have to override the default if you want to run it, like this:

```
$ java -Done-jar.main.class=com.co3.examples.LookupUsername -jar build/libs/co3-caf-examples.jar
```

## Apache Camel Example (java/examples/caf/camel directory)

This project illustrates how you can use Apache Camel to process CAF messages.

The output from the Gradle build is a "One JAR" file (http://one-jar.sourceforge.net) that can easily be run from the command line.  The JAR file produced by the build is build/libs/co3-caf-camel.jar.  

This example uses ~/co3/calcseverity.json as a configuration file.  That is, a calcseverity.json file in the co3 directory within the user's home directory.  This file tells the program how to connect to the Co3 server.  You can use the calcseverity.json.dist file as a starting point.

Once you have the ~/co3/calcseverity.json file configured, you can run the CalculateSeverity program like this:

```
$ java -jar build/libs/co3-caf-camel.jar
```

As with the other examples, you can also run the class from within Eclipse.

See http://camel.apache.org for details on Apache Camel.

## Mulesoft HipChat Example (java/examples/caf/mulesoft/hipchat directory)

This project contains a Mulesoft Anypoint Studio example that reads a message from a queue (Co3 message destination) and posts it to HipChat.  In order to run the example, you will need a HipChat account.  However, even if you don't have HipChat this project can be a useful reference.

See http://www.mulesoft.com for more information about Mulesoft Anypoint Studio.

You need to have Mulesoft Anypoint Studio to run the project.  Anypoint Studio is a freely available commercial product with licenseing restrictions.  Please review the license and consult with an attorney if necessary.

1.  Create the Anypoint Studio project files by running:

    $ gradle studio

2.  Launch Anypoint Studio, then select the File > Import... menu option.  

3.  From the "Select" dialog, select the General > Existing Projects into Workspace option.

4.  From Import Projects, choose the "Select root directory" radio button and click "Browse...".

5.  Select the "hipchat" directory (e.g. java/examples/caf/mulesoft/hipchat) and click "Open".

6.  Click the "Finish" button.  This will open the project.  To see the graphical display 
of the integration's flow, open the src/main/app/mule-config.xml file by double-clicking it.

7.  In order to run the sample, you will need to first create the following Java properties
file:

    ~/co3/co3-hipchat-app.properties

That is, create a "co3" directory in your home directory (e.g. ~/co3) with a file named 
"co3-hipchat-app.properties".  Supply values for the following properties in the file:

  co3.trustStore=<Path to keystore containing trusted certificates>
  co3.trustStorePassword=<keystore password>
  co3.user=<User with which to connect to the Co3 server>
  co3.password=<Password for the Co3 user>
  co3.queueName=<The fully qualified name of the Co3 message destination (e.g. actions.201.mydest)>
  co3.hipChat.room=<The name or ID of the HipChat room>
  co3.hipChat.authToken=<The HipChat authentication token>

8.  Select the Run > Debug > Mule Application menu item to run the integration.  Watch the Console tab for any errors.

# Python Examples (python directory)

This directory contains the Co3 Python client librari (co3 subdirectory) and examples for the CAF and REST APIs (examples subdirectory)

## Certificates
Note that in order to connect to the server, you must provide the server's
CA certificate in a file (e.g. "cacerts.pem").  The quickest way to do this
is to use either openssl or the Java keytool command line utilities.

Using openssl to create the cacerts.pem file (using Linux or Mac OS):

  openssl s_client -connect SERVER:65001 -showcerts -tls1 < /dev/null > cacerts.pem 2> /dev/null

Using keytool to create the cacerts.pem file (Linux, Mac OS or Windows):

  keytool -printcert -rfc -sslserver SERVER:65001 > cacerts.pem

WARNING:  In a production setting, you will definitely want to get the certificate from a trusted source and confirm it's fingerprint.

The host you specify with --host must match exactly the name in the server certificate.  If there is a mismatch, the permanent solution is to either change your DNS server or change the server certificate so it matches.  It is also possible to modify your hosts file temporarily, but that is not a permanent solution.

## Co3 Python Client (python/co3 directory)

The Co3 Python Client (co3 module) is a simple wrapper around the Python requests module that contains tools helpful in calling the Co3 REST API and Custom Action Framework (CAF).

It provides a SimpleClient class that you use to call the Co3 REST API.

It provides an ArgumentParser class (which extends argparse.ArgumentParser) to simplify the writing of command line utilities.  It provides support for arguments such as --host and --email that Co3-oriented command line tools will generally need.

To install this module, run these commands:

  $ python setup.py build
  $ sudo python setup.py install

Note that if you are using Python 3, then use python3 instead of python.

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

This directory contains example CAF processors written in Python.  It assumes have installed the co3 module (see /python/co3/README for instructions on how to install the co3 module).

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

The advanced.py script is similar to basic.py, but it also shows how you can connect back to the Co3 server with the Co3 REST API.  In this example, it simply updates the incident description to include the time.

It is worth noting that when updating an incident, you must consider the possibility that another user has updated the incident.  This script handles that by using the SimpleClient.get_put method, which accepts a function that applys the changes to the incident.  The get_put method does a get, calls the apply function then performs the put.  If the put fails with a 409 Conflict error, then the get/apply/put is tried again.

You start the processor from the command line.  To print the usage, do this:

```
  python advanced.py --help
```

The usage is identical to the basic.py script, except that since it connects to the Co3 server using the REST API, you may need to specify the --org option (if your user is in multiple Co3 organizations).
