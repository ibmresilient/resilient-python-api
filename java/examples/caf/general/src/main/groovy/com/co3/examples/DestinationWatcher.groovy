/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

 package com.co3.examples

import com.co3.activemq.Co3ActiveMQSslConnectionFactory
import org.apache.activemq.transport.TransportFactory
import javax.jms.*

import groovy.json.*
import javax.net.ssl.*
import java.security.KeyStore


/**
 * Helper to watch a JMS destination.
 */
class DestinationWatcher {
    Co3ActiveMQSslConnectionFactory jms

	/**
	 * Creates a new DestinationWatcher.
	 * @param user The user name with which to connect (the email address of the Resilient user).
	 * @param password The password of the user.
	 * @param url The JMS URL, generally of the form:  ssl://HOST:65000
	 */
    DestinationWatcher(String user, String password, String url) {
        jms = new Co3ActiveMQSslConnectionFactory(url)
        
        jms.userName = user
        jms.password = password
	}
	
	/**
	 * Creates a destination watcher with the protocol, host and port specified separately.
	 * @param user The user name with which to connect (the email address of the Resilient user).
	 * @param password The password of the user.
	 * @param useSSL true if you want to use SSL (almost always specify true here).
	 * @param host The host name (of the Resilient server).
	 * @param port The port number of the Resilient server (almost always specify 65000 here).
	 */
    DestinationWatcher(String user, String password, boolean useSSL, String host, int port) {
		this(user, password, "${useSSL ? 'ssl' : 'tcp'}://${host}:${port}")
    }

	/**
	 * Sets the keystore file containing the list of trusted certificates (and it's password).
	 * If you don't call this method, then the JRE's default list of trusted certs will be used.
	 * @param trustStoreFile The keystore file containing the trusted certs.
	 * @param trustStorePassword The password for the keystore file.
	 */
    void setTrustStoreInfo(File trustStoreFile, String trustStorePassword) {
        jms.trustStore = trustStoreFile.canonicalPath
        jms.trustStorePassword = trustStorePassword
    }

	/**
	 * Watch the specified destination name.
	 * 
	 * Note that if the message is successfully processed by the processMessageClosure,
	 * a reply is sent to the Resilient server indicating success.  No error messages are
	 * currently sent (it would be a simple matter to adjust this code to send an error
	 * reply if the closure threw an exception).
	 * 
	 * @param name The full name of the destination (of the form "actions.ORGID.DESTNAME").  For
	 * example, "actions.201.mydest".
	 * @param topic true if the destination is a topic; false if it's a queue.
	 * @param processMessageClosure A closure that takes either 1 or 2 arguments.  The first argument
	 * will be the message text (JSON).  The second argument is the Co3ContextToken (which is needed
	 * if your closure is going to be calling into the Resilient REST API).
	 */
    void watch(String name, boolean topic, Closure processMessageClosure) {
        int maxParms = processMessageClosure.maximumNumberOfParameters

        if (![1, 2].contains(maxParms)) {
            throw new IllegalArgumentException("Closure must contain 1 or 2 arguments")
        }

        Connection con = jms.createConnection()
        
        con.start()

        try {
            Session session = con.createSession(false, Session.CLIENT_ACKNOWLEDGE);

            try {
                Destination dest

                if (topic) {
                    dest = session.createTopic(name)
                } else {
                    dest = session.createQueue(name)
                }

                MessageConsumer consumer = session.createConsumer(dest)

                try {
                    Message message

                    while (null != (message = consumer.receive())) {
                        message.acknowledge()

                        if (maxParms == 1) {
                            processMessageClosure(message.text)
                        } else if (maxParms == 2) {
                            String contextToken = message.getStringProperty("Co3ContextToken")

                            processMessageClosure(message.text, contextToken)
                        }

                        MessageProducer producer = session.createProducer(message.getJMSReplyTo())
                        try {
                            Message reply = session.createTextMessage("Completed the action")
                            reply.setJMSCorrelationID(message.getJMSCorrelationID())
                            reply.setBooleanProperty("Co3InvocationComplete", true)
                            producer.send(reply)
                        } finally {
                            producer.close()
                        }
                    }
                } finally {
                    consumer.close()
                }
            } finally {
                session.close()
            }
        } finally {
            con.close()
        }
    }
}

