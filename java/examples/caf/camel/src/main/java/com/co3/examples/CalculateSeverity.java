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

package com.co3.examples;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;

import org.apache.camel.CamelContext;
import org.apache.camel.Exchange;
import org.apache.camel.Processor;
import org.apache.camel.ProducerTemplate;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.jms.JmsComponent;
import org.apache.camel.impl.DefaultCamelContext;
import org.apache.camel.spi.DataFormat;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;

import com.co3.activemq.Co3ActiveMQSslConnectionFactory;
import com.co3.dto.action.json.ActionAcknowledgementDTO;
import com.co3.dto.action.json.ActionDataDTO;
import com.co3.dto.json.FullIncidentDataDTO;
import com.co3.dto.metadata.json.FieldDefDTO;
import com.co3.dto.metadata.json.FieldDefValueDTO;
import com.co3.simpleclient.ServerConfig;
import com.co3.simpleclient.SimpleClient;
import com.co3.simpleclient.SimpleClient.ApplyChanges;
import com.google.common.base.Predicate;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;

import org.codehaus.jackson.map.DeserializationConfig;

/**
 * Example showing how you can use Apache Camel to process Co3 CAF messages.  This example
 * receives an action message, runs a calculation to determine a new severity then
 * saves the incident with the new severity.
 */
public class CalculateSeverity {
	/**
	 * Provide our own subclass of com.co3.simpleclient.ServerConfig so we can include a queueName property.
	 */
	private static class CalcSeverityServerConfig extends ServerConfig {
		private String queueName;

		public String getQueueName() {
			return queueName;
		}

		@SuppressWarnings("unused")	// This method is used by Jackson when reading the config file.
		public void setQueueName(String queueName) {
			this.queueName = queueName;
		}
		
		public static CalcSeverityServerConfig load(String relativeFileName) throws IOException {
			File file = new File(getDefaultConfigDir(), relativeFileName);
			
			ObjectMapper mapper = new ObjectMapper();
			
			return mapper.readValue(file, CalcSeverityServerConfig.class);
		}
	}

	/**
	 * Specialized Camel DataFormat that allows the use of our internal ObjectMapper, which is a Jackson v1 ObjectMapper. 
	 * The default for Camel is to use a Jackson v2 ObjectMapper, which will not see the annotations properly.
	 */
	private static class Jackson1DataFormat implements DataFormat {
		private ObjectMapper mapper;
		private Class<?> unmarshalType;
		
		private Jackson1DataFormat(Class<?> unmarshalType) {
			mapper = new ObjectMapper();
			
            // If the Co3 server sends something we don't understand, let's ignore it.  Perhaps
            // we have an outdated DTO JAR.
            mapper.configure(DeserializationConfig.Feature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            
			this.unmarshalType = unmarshalType;
		}
		
		@Override
		public void marshal(Exchange exchange, Object graph, OutputStream stream) throws Exception {
			mapper.writeValue(stream, graph);
		}

		@Override
		public Object unmarshal(Exchange exchange, InputStream stream) throws Exception {
			return mapper.readValue(stream, unmarshalType);
		}
	}
	
	/**
	 * The CamelContext used to hold the routes.
	 */
	private CamelContext context = new DefaultCamelContext();
	private CalcSeverityServerConfig serverConfig;
	
	private CalculateSeverity() throws Exception {
		// Load the configuration file that contains the URLs, passwords, etc.
		//
		serverConfig = CalcSeverityServerConfig.load("calcseverity.json");
	
		// Create a connection to the Co3 server.  This will validate the configuration.
		//
		SimpleClient simpleClient = new SimpleClient(serverConfig);

		// The name of the queue we connect to on the server will include the orgId, which we get
		// from the server (via the SimpleClient object).
		//
		final String queueName = String.format("actions.%d.%s", simpleClient.getOrgData().getId(), serverConfig.getQueueName());
	
		// Create the JMS connection factory.  Note that we use the Co3ActiveMQSslConnectionFactory, since 
		// the default ActiveMQSslConnectionFactory does not check the server certificate's common name/subject alt name.
		//
		Co3ActiveMQSslConnectionFactory factory = new Co3ActiveMQSslConnectionFactory(serverConfig.getJmsUrl());
		
		factory.setUserName(serverConfig.getUser());
		factory.setPassword(serverConfig.getPassword());
		factory.setTrustStore(serverConfig.getTrustStore());
		factory.setTrustStorePassword(serverConfig.getTrustStorePassword());
		
		// Add the factory to the CamelContext so it can be used in the routes.
		//
		context.addComponent("co3jms", JmsComponent.jmsComponentAutoAcknowledge(factory));
		
		// Build the route.
		//
		context.addRoutes(new RouteBuilder() {
			// Custom DataFormat that uses Jackson v1 to marshal/unmarshal.  Note that we use the ObjectMapper from
			// the SimpleClient object.
			DataFormat jackson1DataFormat = new Jackson1DataFormat(ActionDataDTO.class);
			String fullQueueName = String.format("co3jms:queue:%s", queueName);
			
			@Override
			public void configure() throws Exception {
				// Read from queue.
				from(fullQueueName)
					// Send to local directory
					.to("file://build/outdir")
			
					// Convert from JSON string to an ActionDataDTO.
					.unmarshal(jackson1DataFormat)

					.process(new Processor() {
						@Override
						public void process(Exchange exchange) throws Exception {
							ActionDataDTO actionData = exchange.getIn().getBody(ActionDataDTO.class);
						
							calcAndSetSeverity(actionData);
						}
					})
					
					// Convert to Co3 ack format.  This content will get automatically sent
					// back to the server because Camel uses the Reply-To JMS header in
					// the message by default.
					.process(new Processor() {
						@Override
						public void process(Exchange exchange) throws Exception {
							exchange.getIn().setBody(newSuccessAckDTO("Everything worked!"));
						}
					})
					
					// Convert ActionAcknowledgementDTO to JSON
					.marshal(jackson1DataFormat);
			}
		});
	}

	/**
	 * Starts listening.
	 * @throws Exception
	 */
	public void start() throws Exception {
		context.start();
	}

	/**
	 * Main entry point for command line invocation.
	 * @param args
	 * @throws Exception
	 */
	public static void main(String [] args) throws Exception {
		CalculateSeverity calcSev = new CalculateSeverity();
		
		calcSev.start();
	}

	/**
	 * Used for testing.  Allows us to simulate the producing of messages.
	 * @return The created Camel ProducerTemplate.
	 */
	ProducerTemplate createProducerTemplate() {
		return context.createProducerTemplate();
	}

	/**
	 * Helper to create a success ActionAcknowledgementDTO.
	 * @param message The text message that you want to appear in the action status in the Co3 UI.
	 * @return An object that can be marshalled (using Jackson v1) into the JSON that the server is expecting.
	 */
	private Object newSuccessAckDTO(String message) {
		ActionAcknowledgementDTO ack = new ActionAcknowledgementDTO();
		
		ack.setComplete(true);
		ack.setMessage("Test DTO message");
		ack.setMessageType(0 /*info*/);
		
		return ack;
	}

	/**
	 * Calculates a new severity with the following rules:
	 * 
	 * - Malware incidents must be at least a Medium priority.
	 * - Denial of Service incidents must be at least a High priority.
	 * 
	 * @param actionData The data from the message queue.
	 */
	private void calcAndSetSeverity(ActionDataDTO actionData) {
		// Determine if the incident is a Malware and/or Denial of Service incident.
		boolean isMalware = false, isDoS = false;
		
		for (int itypeId : actionData.getIncident().getIncidentTypeIds()) {
			// Use the typeInfo to get the value label.
			String label = actionData.getTypeInfo().get("incident").getFields().get("incident_type_ids").getValues().get(String.valueOf(itypeId)).getLabel();
		
			isMalware = isMalware || label.equals("Malware");
			isDoS = isDoS || label.equals("Denial of Service");
		}

		// Get the severity_code field definition/metadata (which includes the valid values).
		SimpleClient simpleClient = new SimpleClient(serverConfig);
		FieldDefDTO field = getField(simpleClient, "incident", "severity_code");
		Integer oldSeverity = actionData.getIncident().getSeverityCode();
		Integer newSeverity = oldSeverity;
		
		if (isDoS) {
			newSeverity = getMaxSeverity(field, oldSeverity, "High");
		} else if (isMalware) {
			newSeverity = getMaxSeverity(field, oldSeverity, "Medium");
		}
		
		if (oldSeverity != newSeverity) {
			String incidentURL = String.format("incidents/%d", actionData.getIncident().getId());
	
			// Set the severity code, taking into consideration that the PUT could return a 409 (conflict)
			// status code if someone else changed it after the GET.  We do this using a get/apply/put
			// pattern.
			class SetSeverityChanger implements ApplyChanges<FullIncidentDataDTO> {
				int newSeverity;
				
				SetSeverityChanger(int newSeverity) {
					this.newSeverity = newSeverity;
				}
				
				@Override
				public void apply(FullIncidentDataDTO input) {
					input.setSeverityCode(newSeverity);
				}
			}
	
			simpleClient.getPut(incidentURL, 
					new SetSeverityChanger(newSeverity),
					FullIncidentDataDTO.class, 
					FullIncidentDataDTO.class);
		}
	}

	/**
	 * Helper to calculate the "maximum" severity.  This function uses the fact that the field definition values
	 * are in ascending order (e.g. "Low" is before "Medium", which is before "High").
	 * @param field The severity_code field.
	 * @param oldSeverity The current severity value (from the incident).
	 * @param newSeverityLabel The label of the 
	 * @return The id/value of the max severity that matches either oldSeverity (by id/value) or newSeverityLabel (by label).
	 */
	private int getMaxSeverity(FieldDefDTO field, final int oldSeverity, final String newSeverityLabel) {
		// Find the max value that matches either oldSeverity by ID or newSeverityLabel by label.
		List<FieldDefValueDTO> reversedValues = Lists.reverse(field.getValues());
		
		return (int) Iterables.find(reversedValues, new Predicate<FieldDefValueDTO>() {
			@Override
			public boolean apply(FieldDefValueDTO input) {
				return input.getValue().equals(oldSeverity) || input.getLabel().equalsIgnoreCase(newSeverityLabel);
			}
		}).getValue();
	}

	/**
	 * Gets the full FieldDefDTO for the specified typeName/fieldName.
	 * @param typeName The type name of interested (e.g. "incident").
	 * @param fieldName The name of the field of interested (e.g. "severity_code").
	 * @return The FieldDefDTO corresponding to the specified typeName/fieldName.
	 * @throws IllegalArgumentException
	 */
	private FieldDefDTO getField(SimpleClient simpleClient, String typeName, String fieldName) {
		String url = String.format("types/%s/fields", typeName);
		
		for (FieldDefDTO field : simpleClient.get(url, new TypeReference<List<FieldDefDTO>>() {})) {
			if (field.getName().equals(fieldName)) {
				return field;
			}
		}
		
		throw new IllegalArgumentException(String.format("Unable to find field %s in type %s", fieldName, typeName));
	}
}
