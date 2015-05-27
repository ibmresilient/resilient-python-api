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

We love to help customers be successful!  Please contact us at [success@resilientsystems.com](mailto:success@resilientsystems.com).

## Python ##

***Where are the Python examples?***

The Python examples are located in the "python" subdirectory.  The following subdirectories exist within that directory:

* `co3` - This directory contains a Python module that is used by all of the Python examples.  You'll probably want to install this module before continuing with the Python examples.  See the [Co3 Python Client](#co3-python-client-pythonco3-directory) section for details.
* `examples/rest` - Examples showing how you can use the Co3 REST API with Python.  See the [Co3 REST API Examples](#co3-rest-api-examples-pythonexamplesrest-directory) section for details.
* `examples/caf` - Examples showing how to use the Co3 CAF with Python.  See the [Co3 CAF Examples](#caf-examples-pythonexamplescaf-directory) section for details.

***Which version of Python do the examples use?***

They should work fine with the latest release of Python 2 or 3.  Python 3 is recommended, however, since it has better support for SSL certificate handling.

***How do I run the Python examples?***

This is discussed in the [Python](#python-examples-python-directory) section below.  

Note that your first step will likely be to install the "co3" Python module.  See the [Co3 Python Client](#co3-python-client-pythonco3-directory) section for more information.

All of the Python examples show a command line usage if you run them with the `--help` argument.  One key point worth calling out here is that you have to somehow tell the example programs how to determine if the server certificate is trusted.  You do this with the `--cafile` argument.  See the [Certificates](#certificates) sub-section for a discussion.

***Where can I find a Python example that just uses the REST API?***

There is such an example in `python/examples/rest/gadget.py`.  This tool is useful for exploring the REST API because it allows you to generally GET/PUT/POST/DELETE to the Co3 server.  See the [Co3 REST API Examples](#co3-rest-api-examples-pythonexamplesrest-directory) section for more information.

***Where can I find a very basic Python CAF example?***

There is a basic Python CAF example in `python/examples/caf/basic.py`.  This example implements a command line interface that allows you to watch a queue/topic.  It simply prints to the console when a message is received.  It also replies to the server with a "Processing complete" completion message.

See the [basic.py](#basicpy) section for more information.

***Where can I find a Python CAF example that connects back to the Co3 server using the REST API?***

There is such an example in `python/examples/caf/advanced.py`.  This example builds on basic.py (mentioned above).  It connects back to the Co3 server to append to the incident's description.  

See the [advanced.py](#advancedpy) section for more information.

## Java ##

***Where are the Java examples?***

The Java examples are in the "java" directory.  The following subdirectories exist within that directory:

* `examples/caf/general` - Groovy examples that read CAF actions from a destination and invoke Co3 REST API commands.  See the [Co3 CAF General Examples](#co3-caf-general-examples-javaexamplescafgeneral) section for details.
* `examples/caf/camel` - Apache Camel example that reads CAF actions from a destination and adjusts the incident severity based on the incident type.  See the [Apache Camel Example](#apache-camel-example-javaexamplescafcamel-directory) section for details.
* `examples/caf/mulesoft` - Mulesoft Anypoint Studio example that illustrates how to read from a message destination and post to HipChat; see the [Mulesoft HipChat Example](#mulesoft-hipchat-example-javaexamplescafmulesofthipchat-directory) section for details.  Note that you will need to install Mulesoft Anypoint Studio to use this example.
* `examples/rest` - A collection of examples that illustrate various ways to use the Co3 REST API.  See the [Co3 REST API Examples](#co3-rest-api-examples-javaexamplesrest-directory) section for details.
* `jms-util` - A library that allows for secure connections to Apache ActiveMQ servers.  See the [Co3 JMS Utilities](#co3-jms-utilities-javajms-util-directory) section for details.  All of the CAF examples use this library because the default Active MQ client library does not check for certificate common name mismatch errors.

***What Java version do the examples use?***

The examples were written using Java 7, although you should be able to run them with Java 6 - 8.

Some of the examples are written in Groovy v2.3.6.

***How do you build the examples?***

We use Gradle to build the examples.  See the [Java Examples](#java-examples-java-directory) section below for more information.

***What's the best way to explore the Java examples?***

We highly recommend that you use Eclipse or IntelliJ for this.  You will need to have the Gradle Eclipse add-in installed.  Once you have done that, you can import the Gradle project in the "java" directory.

***What is Mulesoft?***

Mulesoft is an Enterprise Service Bus (ESB) that allows you to run multiple integrations (Co3-related or not) within a single environment.  An ESB can be helpful if you have many different systems that need to interact with one anohter.  If you already have an ESB, you may want to consider having your Co3 integrations run within it.

The Mulesoft ESB also has a number of pre-built connectors that might simplify integrations with Co3.

See https://www.mulesoft.org for more information on Mulesoft.

See the [Mulesoft HipChat Example](#mulesoft-hipchat-example-javaexamplescafmulesofthipchat-directory) section for an example of how you can use Mulesoft to integrate Co3 with a chat client (HipChat in our example).

If you do not need to full power of an ESB such as Mulesoft, you may wish to consider a lighter-weight alternative such as Apache Camel (see below).

***What is Apache Camel?***

Camel allows you to create "routes" that describe how messages (such as CAF messages) get processed.  Apache Camel is an open source tool with built-in connectors that may help simplify integrations with Co3.

See the [Apache Camel Example](#apache-camel-example-javaexamplescafcamel-directory) section for an example of how you can use Camel to integrate with Co3.
