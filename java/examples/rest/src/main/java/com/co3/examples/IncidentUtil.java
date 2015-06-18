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

package com.co3.examples;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.cli.Option;
import org.apache.commons.cli.OptionGroup;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang.math.NumberUtils;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.joda.time.DateTime;

import com.co3.dto.json.FullIncidentDataDTO;
import com.co3.dto.json.IncidentArtifactDTO;
import com.co3.dto.json.IncidentArtifactTypeDTO;
import com.co3.dto.task.json.TaskDTO;
import com.co3.simpleclient.SimpleClient;
import com.co3.web.rest.json.IdentifierDTO;

/**
 * <p>
 *  Co3IncidentUtil provides a command line interface to various incident-related operations.
 * </p>
 * <p>
 *  If you are here to see the REST API in action, look in the following methods:
 *   <ul>
 *    <li>{@link #createIncident(SimpleClient, String, String)}</li>
 *    <li>{@link #createArtifact(SimpleClient, int, String, String)}</li>
 *    <li>{@link #createTask(SimpleClient, int, String)}</li>
 *    <li>{@link #listIncidents(SimpleClient)}</li>
 *    <li>{@link #listTasks(SimpleClient, int)}</li>
 *   </ul>
 * </p>
 */
public class IncidentUtil {
    private ObjectMapper mapper = new ObjectMapper();
  
    private PrintStream outputStream = System.out;
    
    private static class IncidentUtilOptions extends Co3Options {
        private static final String INCIDENT_ID_ARG = "id";
        private static final String NAME_ARG = "name";
        
        private static final String CREATE_INCIDENT_ARG = "create";
        private static final String INCIDENT_TEMPLATE_ARG = "template";
        
        private static final String LIST_INCIDENTS_ARG = "list";
        
        private static final String CREATE_ARTIFACT_ARG = "createartifact";
        private static final String ARTIFACT_TYPE_ARG = "type";
        private static final String ARTIFACT_VALUE_ARG = "value";
        
        private static final String LIST_TASKS_ARG = "listtasks";
       
        private static final String CREATE_TASK_ARG = "createtask";
        
        private static final String GENERIC_GET_ARG = "get";
        private static final String GLOBAL_GET_ARG = "global";
        
        IncidentUtilOptions() {
            super(IncidentUtil.class.getSimpleName());
        }
        
        @Override
        protected void addOptions(Options options) {
            options.addOption(INCIDENT_TEMPLATE_ARG, 
                    true, 
                    "The name of a JSON file that contains the FullIncidentDataDTO data to send to the server (only applies if -create is specified)");
            options.addOption(NAME_ARG, true, "The name to use to create the incident/task");
            options.addOption(ARTIFACT_TYPE_ARG, true, "The type of the artifact to add");
            options.addOption(ARTIFACT_VALUE_ARG, true, "The value of the artifact to add (e.g. the IP address, DNS name, etc.)");
            options.addOption(GLOBAL_GET_ARG, false, "Perform the operation without prepending the organization URL (useful if you want to get something that is outside of the org, like /rest/const)");
            
            Option incIdOption = new Option(INCIDENT_ID_ARG, true, "The ID of the incident to operate on");
            incIdOption.setType(Number.class);
            options.addOption(incIdOption);
           
            OptionGroup commandOptions = new OptionGroup();
            
            commandOptions.addOption(new Option(CREATE_INCIDENT_ARG, false, "Create an incident"));
            commandOptions.addOption(new Option(LIST_INCIDENTS_ARG, false, "List incidents"));
            commandOptions.addOption(new Option(CREATE_ARTIFACT_ARG, false, "Add an artifact to the incident (incident ID must be specified with -id)"));
            commandOptions.addOption(new Option(LIST_TASKS_ARG, false, "Lists all the tasks on an incident"));
            commandOptions.addOption(new Option(CREATE_TASK_ARG, false, "Creates a task on an incident"));
            commandOptions.addOption(new Option(GENERIC_GET_ARG, true, "Performs a GET operation on the specified URL"));
            
            options.addOptionGroup(commandOptions);
        }

        public boolean isCreateIncident() {
            return hasConfigValue(CREATE_INCIDENT_ARG);
        }

        public String getName() {
            String name = getConfigValue(NAME_ARG);
            
            if (StringUtils.isBlank(name)) {
                throw new IllegalArgumentException(String.format("-%s must be specified", NAME_ARG));
            }
            return name;
        }

        public boolean isListIncidents() {
            return hasConfigValue(LIST_INCIDENTS_ARG);
        }

        public String getIncidentTemplateArg() {
            return getConfigValue(INCIDENT_TEMPLATE_ARG);
        }

        public boolean isCreateArtifact() {
            return hasConfigValue(CREATE_ARTIFACT_ARG);
        }

        public Number getIncidentId() {
            String id = getConfigValue(INCIDENT_ID_ARG);
          
            if (id == null) {
                throw new IllegalArgumentException(String.format("-%s argument is required", INCIDENT_ID_ARG));
            } else if (NumberUtils.isNumber(id)) {
                return NumberUtils.createNumber(id);
            }
            
            throw new IllegalArgumentException(String.format("Invalid -%s option:  %s", INCIDENT_ID_ARG, id));
        }

        public String getArtifactValue() {
            String artifactValue = getConfigValue(ARTIFACT_VALUE_ARG);
            if (artifactValue == null) {
                throw new IllegalArgumentException(String.format("-%s must be specified when creating artifacts", ARTIFACT_VALUE_ARG));
            }
            return artifactValue;
        }

        public String getArtifactType() {
            String artifactType = getConfigValue(ARTIFACT_TYPE_ARG);
            if (artifactType == null) {
                throw new IllegalArgumentException(String.format("-%s must be specified when creating artifacts", ARTIFACT_TYPE_ARG));
            }
            return artifactType;
        }

        public boolean isListTasks() {
            return hasConfigValue(LIST_TASKS_ARG);
        }

        public boolean isCreateTasks() {
            return hasConfigValue(CREATE_TASK_ARG);
        }

        public boolean isGenericGet() {
            return hasConfigValue(GENERIC_GET_ARG);
        }

        public boolean isGlobalGet() {
            return hasConfigValue(GLOBAL_GET_ARG);
        }
        
        public String getGenericGetURL() {
            return getConfigValue(GENERIC_GET_ARG);
        }
    }
    
    private IncidentUtilOptions options = new IncidentUtilOptions();
    
    /**
     * Package constructor only used from {@link #main(String[])} (and tests).
     */
    IncidentUtil(PrintStream outputStream) {
        this.outputStream = outputStream;
    }
   
    /**
     * Creates an incident using the Resilient REST API and writes the server response to stdout.
     * 
     * @param client The client object to use to make the requests.
     * @param inputTemplateFileName The name of a JSON file to use as an incident template.  Specifying null
     * will indicate that the default values should be used (these are defaults specified by this sample...they are
     * not necessarily "system defaults").  See IncidentTemplate.json for the defaults.  If you specify a templateFileName,
     * it must be a JSON-formatted file that can be read into a {@link FullIncidentDataDTO}.
     * @param incidentName The name the incident should have.  Specify null to use whatever value is in the template.  A
     * non-null value will override the value specified in the template.
     * 
     * @throws IOException If the template cannot be read or if there was an error translating the server's response.
     */
    void createIncident(SimpleClient client, String inputTemplateFileName, String incidentName) throws IOException {
        FullIncidentDataDTO incidentTemplate = loadIncidentTemplate(inputTemplateFileName);
     
        if (incidentName != null) {
            incidentTemplate.setName(incidentName);
        }
        
        incidentTemplate.setDiscoveredDate(new Date());
        
        String incidentsURI = client.getOrgURL("/incidents?want_full_data=true");
        
        Map<String, Object> createdIncident = client.post(incidentsURI, incidentTemplate, new TypeReference<HashMap<String, Object>>(){});
      
        writeOutput(client, createdIncident);
    }

    /**
     * Lists all of the incidents the user has permission to see to stdout.
     * 
     * @param client The client object to use to make the requests.
     *
     * @throws IOException If there was an error translating the server's response.
     */
    void listIncidents(SimpleClient client) throws IOException {
        String incidentsURI = client.getOrgURL("/incidents?want_closed=false");
        
        List<Map<String, Object>> smallIncidents = client.get(incidentsURI, new TypeReference<List<Map<String, Object>>>(){});
        
        writeOutput(client, smallIncidents);
    }
  
    /**
     * Creates an artifact on an incident.  The added artifact is written to stdout.
     * 
     * @param client The client object to use to make the requests.
     * @param incidentId The ID of the incident to which the artifact will be attached.
     * @param artifactType The name of the artifact type (e.g. "IP Address", "DNS Name", etc.).
     * @param artifactValue The value of the artifact (i.e. the actual IP address, DNS name, etc.).
     * 
     * @throws IOException If there was an error translating the server's response.
     */
    void createArtifact(SimpleClient client, int incidentId, String artifactType, String artifactValue) throws IOException {
        int artifactTypeId = findArtifactTypeId(client, artifactType);
        
        IncidentArtifactDTO artifact = new IncidentArtifactDTO();
        
        artifact.setType(artifactTypeId);
        artifact.setValue(artifactValue);
       
        String artifactsURI = client.getOrgURL(String.format("/incidents/%d/artifacts", incidentId));
        
        List<Map<String, Object>> artifacts = client.post(artifactsURI, artifact, new TypeReference<List<Map<String, Object>>>(){});
       
        writeOutput(client, artifacts);
    }
 
    /**
     * Lists an incident's tasks to stdout.
     * 
     * @param client The client object to use to make the requests.
     * @param incidentId The ID of the incident whose tasks are to be listed.
     * @throws IOException If there was an error translating the server's response.
     */
    void listTasks(SimpleClient client, int incidentId) throws IOException {
        String tasksURI = client.getOrgURL(String.format("/incidents/%d/tasks", incidentId));
        
        List<Map<String, Object>> tasks = client.get(tasksURI, new TypeReference<List<Map<String, Object>>>(){});
        
        writeOutput(client, tasks);
    }
   
    /**
     * Creates a task on an incident.  Details about the added task are written to stdout.
     * 
     * @param client The client object to use to make the requests.
     * @param incidentId
     * @param name
     * @throws IOException If there was an error translating the server's response.
     */
    void createTask(SimpleClient client, int incidentId, String name) throws IOException {
        TaskDTO task = new TaskDTO();
        
        task.setName(name);
        task.setActive(true);
        task.setCustomInstructions("<html><ul><li>Instruction #1</li><li>Instruction #2</li></ul></html>");
        task.setDescription("This is a sample task description");
        
        // Make the task due in 7 days.
        //
        task.setDueDate(new DateTime().plusDays(7).toDate());
       
        // Create the task.  Note that tasksURI is under /rest/orgs/{orgId}/incidents/{incId}/tasks
        // when posting, but is under /rest/orgs/{orgId}/tasks when getting.
        //
        String tasksURI = client.getOrgURL(String.format("/incidents/%d/tasks", incidentId));
       
        IdentifierDTO<Integer> taskId = client.post(tasksURI, task, new TypeReference<IdentifierDTO<Integer>>(){});
       
        // Get the newly created task (separate step since GET /rest/orgs/.../tasks/{taskId} does not
        // currently echo back the task).
        //
        String taskURI = client.getOrgURL(String.format("/tasks/%d", taskId.getId()));
      
        Map<String, Object> loadedTask = client.get(taskURI, new TypeReference<Map<String, Object>>(){});
        
        writeOutput(client, loadedTask);
    }
 
    /**
     * Performs a GET operation on the specified relativeUrl and writes the output using the specified
     * to standard output.
     * @param client The client object to use to make the requests.
     * @param relativeUrl The URL to use.
     * @throws IOException
     */
    void get(SimpleClient client, String relativeUrl) throws IOException {
        String url = options.isGlobalGet() ? relativeUrl : client.getOrgURL(relativeUrl);
        
        Object response = client.get(url, new TypeReference<Object>(){});
        
        writeOutput(client, response);
    }
    
    /**
     * Parses the command line arguments and runs whatever command is specified.
     * @param args The command line arguments (from main).
     * @throws IOException If there is a problem reading or writing.
     * @throws ParseException If there is a problem with the command line arguments.
     */
    private void run(String [] args) throws IOException, ParseException {
        options.parse(args);
        
        Co3Options.PasswordInfo info = options.getPasswordInfo();
        
        SimpleClient client = new SimpleClient(options.getBaseURL(), options.getOrgName(), info.getEmail(), info.getPassword());
        
        if (options.isCreateIncident()) {
            String name = options.getName();
           
            createIncident(client, options.getIncidentTemplateArg(), name);
        } else if (options.isListIncidents()) {
            listIncidents(client);
        } else if (options.isCreateArtifact()) {
            Number id = options.getIncidentId();
            String artifactValue = options.getArtifactValue();
            String artifactType = options.getArtifactType();
            
            createArtifact(client, id.intValue(), artifactType, artifactValue);
        } else if (options.isListTasks()) {
            Number id = options.getIncidentId();
            
            listTasks(client, id.intValue());
        } else if (options.isCreateTasks()) {
            Number id = options.getIncidentId();
            String name = options.getName();
            
            createTask(client, id.intValue(), name);
        } else if (options.isGenericGet()) {
            String url = options.getGenericGetURL();
            
            get(client, url);
        }
    }
   
    /**
     * Loads FullIncidentDataDTO template object from the specified fileName (or from the built-in internal
     * default template).
     * @param fileName The name of the file to load.  If this is null, a default template is loaded.
     * @return A FullIncidentDataDTO template that can be used to create an incident.
     * @throws IOException If there's a problem reading the file.
     */
    private FullIncidentDataDTO loadIncidentTemplate(String fileName) throws IOException {
        InputStream templateStream = null;
         
        if (fileName == null) {
            templateStream = getClass().getClassLoader().getResourceAsStream("IncidentTemplate.json");
        } else {
            templateStream = new FileInputStream(fileName);
        }
        
        try {
            if (templateStream == null) {
                throw new IllegalStateException("Unable to load template");
            }
            
            return mapper.readValue(templateStream, FullIncidentDataDTO.class);
        } finally {
            if (templateStream != null) {
                templateStream.close();
            }
        }
    }
   
    /**
     * Main entry point to the Co3IncidentUtil class. 
     * @param args Command line arguments.
     * @throws IOException If there is a problem reading or writing.
     * @throws ParseException If there is a problem with the command line arguments.
     */
    public static void main(String [] args) throws ParseException, IOException {
        new IncidentUtil(System.out).run(args);
    }
    
    /**
     * Locates an artifact type ID given it's name.
     * @param client The client object to use to make the requests.
     * @param artifactTypeName The name of the artifact type (e.g. "IP Address", "DNS Name", etc.).  A case insensitive
     * match is done.
     * @return The ID of the artifact type.
     * @throws IllegalArgumentException If the artifact type does not exist.
     */
    private int findArtifactTypeId(SimpleClient client, String artifactTypeName) {
        for (IncidentArtifactTypeDTO artifactType : client.getConstData().getArtifactTypes()) {
            if (artifactType.getName().equalsIgnoreCase(artifactTypeName)) {
                return artifactType.getId();
            }
        }
        
        throw new IllegalArgumentException(String.format("Unsupported artifact type:  %s", artifactTypeName));
    }
    
    /**
     * Helper to write output of an object.
     * @param client The client to use in case we need to get more data.
     * @param obj The object to export.
     * @throws IOException
     */
    private void writeOutput(SimpleClient client, Object obj) throws IOException {
        outputStream.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(obj));
    }
}
