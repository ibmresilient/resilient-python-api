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

import static org.junit.Assert.assertEquals;
import static org.mockito.Matchers.any;
import static org.mockito.Matchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.util.List;
import java.util.Map;

import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.junit.Test;

import com.co3.dto.json.ConstDTO;
import com.co3.dto.json.IncidentArtifactTypeDTO;
import com.co3.simpleclient.SimpleClient;
import com.co3.web.rest.json.IdentifierDTO;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

public class IncidentUtilTest {
    
    private ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
    private PrintStream printStream = new PrintStream(outputStream, true /*autoFlush*/);
    private IncidentUtil util = new IncidentUtil(printStream);
    private static final int ORG_ID = 54321;
    private static final String IP_ADDRESS_NAME = "IP Address";
    private ObjectMapper mapper = new ObjectMapper();
    
    @SuppressWarnings("unchecked")
    private void configureMockClient(SimpleClient client, boolean isGet, String relativeUrl, Object response) {
        String actualUrl = String.format("/orgs/%d%s", ORG_ID, relativeUrl);
        
        when(client.getOrgURL(relativeUrl)).thenReturn(actualUrl);
        
        if (isGet) {
            when(client.get(eq(actualUrl), any(TypeReference.class))).thenReturn(response);
        } else {
            when(client.post(eq(actualUrl), any(Object.class), any(TypeReference.class))).thenReturn(response);
        }
    }
   
    private void verifyExpectedResponse(Object expected, OutputStream actualData) throws IOException {
    	Object actual = mapper.readValue(new String(outputStream.toByteArray()), expected.getClass());
    	
    	assertEquals(expected, actual);
    }
    
    @Test
    public void testGet() throws IOException {
        String relativeUrl = "/incidents/1234";
        
        Map<String, Object> response = Maps.newHashMap();
       
        response.put("name", "some test name");
        
        SimpleClient client = mock(SimpleClient.class);
       
        configureMockClient(client, true /*isGet*/, relativeUrl, response);
        
        util.get(client, relativeUrl);
      
        verifyExpectedResponse(response, outputStream);
    }
    
    @Test
    public void testCreateTask() throws IOException {
        int incId = 1234;
        int taskId = 54321;
        String relativeUrlForPost = String.format("/incidents/%d/tasks", incId);
        String taskName = "My Test Task";
       
        IdentifierDTO<Integer> response = new IdentifierDTO<Integer>();
        response.setId(taskId);
        
        SimpleClient client = mock(SimpleClient.class);
       
        configureMockClient(client, false /*isGet=false*/, relativeUrlForPost, response);
     
        String relativeUrlForGet = String.format("/tasks/%d", taskId);
        
        Map<String, Object> task = Maps.newHashMap();
        task.put("name", taskName);
        
        configureMockClient(client, true /*isGet*/, relativeUrlForGet, task);
        
        util.createTask(client, incId, taskName);
       
        verifyExpectedResponse(task, outputStream);
    }
    
    @Test
    public void testListTasks() throws IOException {
        int incId = 383838;
        String relativeUrl = String.format("/incidents/%d", incId);
        
        List<Map<String, Object>> response = Lists.newArrayList();
       
        response.add(ImmutableMap.<String, Object>builder().put("name", "Task1").build());
        response.add(ImmutableMap.<String, Object>builder().put("name", "Task2").build());
        
        SimpleClient client = mock(SimpleClient.class);
       
        configureMockClient(client, true /*isGet*/, relativeUrl, response);
        
        util.get(client, relativeUrl);
        
        verifyExpectedResponse(response, outputStream);
    }
    
    @Test
    public void testCreateArtifact() throws IOException {
        int incId = 383838;
        String relativeUrl = String.format("/incidents/%d/artifacts", incId);
        
        SimpleClient client = mock(SimpleClient.class);
     
        ConstDTO constData = new ConstDTO();
        IncidentArtifactTypeDTO type = new IncidentArtifactTypeDTO();
        type.setName(IP_ADDRESS_NAME);
        type.setId(1);
        constData.setArtifactTypes(Lists.newArrayList(type));
        
        when(client.getConstData()).thenReturn(constData);
        
        List<Map<String, Object>> response = Lists.newArrayList();
       
        response.add(ImmutableMap.<String, Object>builder().put("value", "192.168.0.1").build());
        response.add(ImmutableMap.<String, Object>builder().put("value", "192.168.0.2").build());
        
        configureMockClient(client, false /*isGet=false*/, relativeUrl, response);
        
        util.createArtifact(client, incId, IP_ADDRESS_NAME, "192.168.0.1 192.168.0.2");
        
        verifyExpectedResponse(response, outputStream);
    }
    
    @Test
    public void testListIncidents() throws IOException {
        String relativeUrl = "/incidents";
        
        List<Map<String, Object>> response = Lists.newArrayList();
       
        response.add(ImmutableMap.<String, Object>builder().put("name", "Inc #1").build());
        response.add(ImmutableMap.<String, Object>builder().put("name", "Inc #2").build());
        
        SimpleClient client = mock(SimpleClient.class);
       
        configureMockClient(client, true /*isGet*/, relativeUrl, response);
        
        util.get(client, relativeUrl);
        
        verifyExpectedResponse(response, outputStream);
    }
    
    @Test
    public void testCreateIncident() throws IOException {
        String relativeUrl = "/incidents?want_full_data=true";
        String name = "My Test Incident";
        
        Map<String, Object> response = Maps.newHashMap();
      
        response.put("name", name);
        
        SimpleClient client = mock(SimpleClient.class);
       
        configureMockClient(client, false /*isGet=false*/, relativeUrl, response);
        
        util.createIncident(client, null, name);
        
        verifyExpectedResponse(response, outputStream);
    }
}
