
# Java Examples (java directory)

The Java examples can be built using the Gradle build system (see http://www.gradle.org).  To build them, you simply cd into the java directory and type:
```
$ gradle build
```

However, it is generally more useful to see the examples from within an IDE.  You can import the Gradle project into Eclipse if you have the Gradle Integration for Eclipse installed.  It also assumes that you have Groovy support installed into Eclipse.

## Resilient REST API Examples (java/examples/rest directory)

This project contains sample command line utilities that use the Resilient REST API (and SimpleClient class).

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

## JMS Utilities (java/jms-util directory)

The current version of the ActiveMQ client library (5.10.0) does no validate that the host name you think you're connecting to is actually what is in the certificate commonName or subjectAltName (see https://issues.apache.org/jira/browse/AMQ-5443 for details).

To workaround this issue, Resilient has provided a Co3ActiveMQSslConnectionFactory class that checks the host name.  Using this Co3ActiveMQSslConnectionFactory directly in Java code is relatively straightforward:

```
Co3ActiveMQSslConnectionFactory factory = new Co3ActiveMQSslConnectionFactory("ssl://co3:65000");

factory.setUserName("user@mycompany.com");
factory.setPassword("userpassword");
factory.setTrustStore("keystore");
factory.setTrustStorePassword("password");

Connection con = factory.createConnection();

...

```

There is an example of how this would translate to Mulesoft/Spring in the `java/examples/caf/mulesoft/hipchat` directory.

In general, when connecting to a the Resilient server using JMS you should use the Co3ActiveMQSslConnectionFactory class to avoid man-in-the-middle vulnerabilities.  That is, unless you have some other way to ensure the integrity of the SSL connection.

## Resilient CAF General Examples (java/examples/caf/general)

This project contains example Groovy code to interact with message destinations.  The following table describes each example Groovy class in detail:

Class Name           | Description
-------------------- | -----------
DestinationWatcher   | A helper class that simplifies connecting to and reading from message destinations.
WatchDestination     | A command line tool that uses DestinationWatcher.  This can be used to test that messages are being sent to a destination.
LookupUsername       | A command line tool that watches a destination for "user name" artifact changes and updates them using the Resilient REST API.

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

This example uses ~/co3/calcseverity.json as a configuration file.  That is, a calcseverity.json file in the co3 directory within the user's home directory.  This file tells the program how to connect to the Resilient server.  You can use the calcseverity.json.dist file as a starting point.

Once you have the ~/co3/calcseverity.json file configured, you can run the CalculateSeverity program like this:

```
$ java -jar build/libs/co3-caf-camel.jar
```

As with the other examples, you can also run the class from within Eclipse.

See http://camel.apache.org for details on Apache Camel.

## Mulesoft HipChat Example (java/examples/caf/mulesoft/hipchat directory)

This project contains a Mulesoft Anypoint Studio example that reads a message from a queue (Resilient message destination) and posts it to HipChat.  In order to run the example, you will need a HipChat account.  However, even if you don't have HipChat this project can be a useful reference.

See http://www.mulesoft.com for more information about Mulesoft Anypoint Studio.

You need to have Mulesoft Anypoint Studio to run the project.  Anypoint Studio is a freely available commercial product with licenseing restrictions.  Please review the license and consult with an attorney if necessary.

1.  Create the Anypoint Studio project files by running:
```
    $ gradle studio
```
2.  Launch Anypoint Studio, then select the File > Import... menu option.  

3.  From the "Select" dialog, select the General > Existing Projects into Workspace option.

4.  From Import Projects, choose the "Select root directory" radio button and click "Browse...".

5.  Select the "hipchat" directory (e.g. `java/examples/caf/mulesoft/hipchat`) and click "Open".

6.  Click the "Finish" button.  This will open the project.  To see the graphical display
of the integration's flow, open the src/main/app/mule-config.xml file by double-clicking it.

7.  In order to run the sample, you will need to first create the following Java properties
file:

    ~/co3/co3-hipchat-app.properties

That is, create a "co3" directory in your home directory (e.g. ~/co3) with a file named
"co3-hipchat-app.properties".  Supply values for the following properties in the file:
```
  co3.trustStore=<Path to keystore containing trusted certificates>
  co3.trustStorePassword=<keystore password>
  co3.user=<User with which to connect to the Resilient server>
  co3.password=<Password for the Resilient user>
  co3.queueName=<The fully qualified name of the Resilient message destination (e.g. actions.201.mydest)>
  co3.hipChat.room=<The name or ID of the HipChat room>
  co3.hipChat.authToken=<The HipChat authentication token>
```

8.  Select the Run > Debug > Mule Application menu item to run the integration.  Watch the Console tab for any errors.
