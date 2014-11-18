/*
 * Co3 Systems, Inc. ("Co3") is willing to license software or access to 
 * software to the company or entity that will be using or accessing the 
 * software and documentation and that you represent as an employee or 
 * authorized agent ("you" or "your" only on the condition that you 
 * accept all of the terms of this license agreement.
 *
 * The software and documentation within Co3's Development Kit are 
 * copyrighted by and contain confidential information of Co3. By 
 * accessing and/or using this software and documentation, you agree 
 * that while you may make derivative works of them, you:
 * 
 * 1)   will not use the software and documentation or any derivative 
 *      works for anything but your internal business purposes in 
 *      conjunction your licensed used of Co3's software, nor
 * 2)   provide or disclose the software and documentation or any 
 *      derivative works to any third party.
 * 
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 * ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package com.co3.examples

import groovy.json.JsonSlurper

def cli = new CliBuilder(usage:'WatchDestination.groovy [options] destination_name')

final int DEFAULT_PORT = 65000

cli.user(args:1, required:true, argName:'user', 'Use user to authenticate (required)')
cli.server(args:1, required:true, argName:'server', 'Connect to this server (required)')
cli.topic(argName:'topic', 'destination_name is a topic (if not specified then destination_name is assumed to be a queue)')
cli.port(args:1, argName:'port', "Connect to this port (default: ${DEFAULT_PORT})")
cli.verbose(argName:'verbose', "Print out extra information (e.g. the full JSON output string)")
cli.nossl(argName:'nossl', "Do not use SSL when connecting to server")
cli.password(args:1, argName:'password', "WARNING:  This is insecure because the password will appear in the command history and to other processes.")
cli.truststore(args:1, argName:'truststore', "Java keystore file containing trusted certificates")
cli.truststorepassword(args:1, argName:'truststorepassword', "Password for -truststore argument")

def options = cli.parse(args)

if (options == null) {
	// Usage already printed.
	System.exit(1)
} else if (options.arguments().isEmpty()) {
	System.err.println("destination_name is required")
	cli.usage()
	System.exit(1)
} else if (options.arguments().size() > 1) {
	System.err.println("Only one destination_name can be specified:  ${options.arguments()}")
	cli.usage()
	System.exit(1)
}

String destinationName = options.arguments()[0]
String password

if (options.password) {
	password = options.password
} else {
	if (System.console()) {
		password = new String(System.console().readPassword("Password: "))
	} else {
		System.err.println("Unable to read password because System.console() is null, which means you're probably running from within Eclipse or some other container")
		System.exit(1)	
	}
}

int port = options.port ? Integer.valueOf(options.port) : DEFAULT_PORT
boolean useSSL = options.nossl ? false : true

DestinationWatcher watcher = new DestinationWatcher(options.user, password, useSSL, options.server, port)

if (options.truststore) {
	String keystorePassword = options.truststorepassword ? options.truststorepassword : "changeit"
	File keystore = new File(options.truststore)

	watcher.setTrustStoreInfo(keystore, keystorePassword)
}

watcher.watch destinationName, options.topic, { String messageText, String contextToken ->
	def obj = new JsonSlurper().parseText(messageText)

	println "Received message"

	if (options.verbose) {
		println messageText
	}

	// Convert the IDs to names using the metadata.
	def itypeLabels = obj.incident.incident_type_ids.collect {
		obj.type_info.incident.fields.incident_type_ids.values[it.value.toString()].label
	}

	println "\tIncident ID:     ${obj.incident.id}"
	println "\tIncident name:   ${obj.incident.name}"
	println "\tIncident types:  ${itypeLabels.join(', ')}"

	if (obj.artifact) {
		println "\tArtifact:        ${obj.artifact.value}"
	}
	println "\tContext token:   ${contextToken}"
}
