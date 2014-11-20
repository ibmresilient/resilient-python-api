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

package com.co3.simpleclient;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.security.KeyManagementException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.net.ssl.SSLContext;

import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.HttpHeaders;
import org.apache.http.HttpResponse;
import org.apache.http.HttpStatus;
import org.apache.http.StatusLine;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.methods.HttpRequestBase;
import org.apache.http.conn.ssl.SSLConnectionSocketFactory;
import org.apache.http.conn.ssl.SSLContexts;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.HttpClientBuilder;
import org.codehaus.jackson.map.DeserializationConfig;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;

import com.co3.dto.json.ConstDTO;
import com.co3.dto.json.FullOrgDTO;
import com.co3.dto.json.SessionOrgInfoDTO;
import com.co3.dto.json.UserSessionDTO;
import com.co3.web.rest.json.AuthenticationDTO;
import com.google.common.base.Charsets;
import com.google.common.collect.Lists;
import com.google.common.io.CharStreams;
import com.google.common.net.MediaType;

/**
 * <p>The SimpleClient class can be used to interact with a Co3 server.  Example:</p>
 * <code>
 *      String orgName = "Acme Widgets";    // can be null if the user only has access to one Org.
 *      SimpleClient client = new SimpleClient("https://sir.co3sys.com", null, "user@company.com", "SomePassword!");
 *      
 *      List<IncidentDTO> incidents = client.get(client.getOrgURL("/incidents"), new TypeReference<List<IncidentDTO>>(){});
 * </code>
 */
public class SimpleClient {
   
    /**
     * The base URL to use to connect to the server (e.g. https://app.co3sys.com).
     */
    private URL baseURL;
    
    /**
     * The name of the organization to operate on (can be null if the user is only in one org).
     */
    private String orgName;
    
    /**
     * The email address of the user who is to perform the operation.
     */
    private String email;
    
    /**
     * The password of the user who is to perform the operation.
     */
    private String password;
   
    /**
     * The user session information.  This is returned by the Co3 server after successful
     * authentication.
     */
    private UserSessionDTO sessionInfo;
    
    /**
     * Constant data from the server (e.g. artifact types, data types, etc.)
     */
    private ConstDTO constData = null;
    
    /**
     * Apache HttpClient object that's used to interact with the Co3 server.
     */
    private HttpClient httpClient = null;
    
    /**
     * Jackson ObjectMapper that's used to convert objects to/from JSON.
     */
    private ObjectMapper mapper = newObjectMapper();

    /**
     * The Co3ContextHeader received from the custom actions framework.
     */
    private String contextHeader = null;

    /**
     * The Java keystore to use for trusting certificates.
     */
    private KeyStore trustStore = null;
    
    /**
     * Exception for holding HTTP exception.
     */
    public class SimpleHTTPException extends RuntimeException {
        private static final long serialVersionUID = 7859659271453558812L;
        
        private int statusCode;
        
        private SimpleHTTPException(int statusCode, String message) {
            super(message);
            
            this.statusCode = statusCode;
        }

        public int getStatusCode() {
            return statusCode;
        }
    }
    
    /**
     * Method factory to create HttpGet, HttpPut, etc. objects
     * given a URL.  This exists to aid in testing.
     */
    class SimpleHttpFactory {
        HttpClient newHttpClient() {
            try {
                SSLContext sslcontext = SSLContexts.custom()
                    .loadTrustMaterial(trustStore)
                    .build();
            
                // Allow TLS protocol only.  Also use browser-compatible hostname verification.
                SSLConnectionSocketFactory sslsf = new SSLConnectionSocketFactory(
                        sslcontext,
                        new String[] { "TLSv1" },
                        null,
                        SSLConnectionSocketFactory.BROWSER_COMPATIBLE_HOSTNAME_VERIFIER);    
                
                 return HttpClientBuilder.create().setSSLSocketFactory(sslsf).build();
            } catch (KeyManagementException | NoSuchAlgorithmException | KeyStoreException e) {
                throw new IllegalArgumentException("Unable to initialize SSL", e);
            }
        }
        
        HttpGet newGet(URL url) {
            return new HttpGet(url.toExternalForm());
        }
        
        HttpPut newPut(URL url) {
            return new HttpPut(url.toExternalForm());
        }
        
        HttpPost newPost(URL url) {
            return new HttpPost(url.toExternalForm());
        }
        
        HttpDelete newDelete(URL url) {
            return new HttpDelete(url.toExternalForm());
        }
    }
   
    /**
     * Constructs a new SimpleClient object.  The server is contacted to authenticate the user
     * before this constructor returns.
     * 
     * @param baseURL The base URL to use (e.g. "https://app.co3sys.com").
     * @param orgName The name of the organization to operate on (can be null if the user is only in one org).
     * @param email The user's email address.
     * @param password The user's password.
     */
    public SimpleClient(URL baseURL, String orgName, String email, String password) {
        this(baseURL, orgName, email, password, null /*trustedStoreFile*/, null /*trustedStorePassword*/);
    }
    
    /**
     * Constructs a new SimpleClient object.  The server is contacted to authenticate the user
     * before this constructor returns.
     * 
     * @param baseURL The base URL to use (e.g. "https://app.co3sys.com").
     * @param orgName The name of the organization to operate on (can be null if the user is only in one org).
     * @param email The user's email address.
     * @param password The user's password.
     * @param trustedStore A Java keystore that contains the list of trusted CA certificates.
     * @param trustedStorePassword The password for trustedStore.
     */
    public SimpleClient(URL baseURL, String orgName, String email, String password, File trustedStoreFile, String trustedStorePassword) {
    	init(baseURL, orgName, email, password, trustedStoreFile, trustedStorePassword);
    }

    /**
     * Creates a SimpleClient with a ServerConfig object bean.
     * @param config An object containing the configuration data.
     * @throws MalformedURLException
     */
    public SimpleClient(ServerConfig config) throws MalformedURLException {
		URL baseURL = new URL(config.getRestUrl());
		File trustStore = new File(config.getTrustStore());
		
		init(baseURL, config.getOrgName(), config.getUser(), config.getPassword(), trustStore, config.getTrustStorePassword());
    }
   
    private void init(URL baseURL, String orgName, String email, String password, File trustedStoreFile, String trustedStorePassword) {
        this.baseURL = baseURL;
        this.orgName = orgName;
        this.email = email;
        this.password = password;
      
        if (trustedStoreFile != null) {
            try (FileInputStream instream = new FileInputStream(trustedStoreFile)) {
                trustStore = KeyStore.getInstance(KeyStore.getDefaultType());
                
                trustStore.load(instream, trustedStorePassword.toCharArray());
            } catch (NoSuchAlgorithmException | CertificateException | IOException | KeyStoreException e) {
                throw new IllegalArgumentException("Unable to load trust store", e);
            }
        }
        
        connect();
    }
   
    /*
     * Creates the Jackson ObjectMapper.
     */
    private ObjectMapper newObjectMapper() {
    	ObjectMapper mapper = new ObjectMapper();
    	
        // If the Co3 server sends something we don't understand, let's ignore it.  Perhaps
        // we have an outdated DTO JAR.
        mapper.configure(DeserializationConfig.Feature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        return mapper;
    }
    
    /**
     * Sets the X-Co3ContextToken header  This is important if you are using this SimpleClient
     * object to respond to actions.
     * @param contextHeader The header value.
     */
    public void setContextHeader(String contextHeader) {
        this.contextHeader = contextHeader;
    }
  
    private <T> T get(String relativeURL, ReturnProcessor<T> processor) {
        HttpGet get = getSimpleHttpFactory().newGet(getURL(relativeURL));
        
        return executeRequest(get, processor);
    }
    
    /**
     * Performs a GET operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * <code>
     *  List<IncidentDTO> incidents = client.get(client.getOrgURL("/incidents"), new TypeReference<List<IncidentDTO>>(){});
     * </code>
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param returnType The type that is expected to be returned.
     * @return The returned object, parsed into the specified returnType.
     */
    public <T> T get(String relativeURL, TypeReference<T> returnType) {
        return get(relativeURL, new TypeReferenceReturnProcessor<T>(returnType));
    }
 
    /**
     * Performs a GET operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * <code>
     *  List<IncidentDTO> incidents = client.get(client.getOrgURL("/incidents"), new TypeReference<List<IncidentDTO>>(){});
     * </code>
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param returnClass The type that is expected to be returned.
     * @return The returned object, parsed into the specified returnClass.
     */
    public <T> T get(String relativeURL, Class<T> returnClass) {
        return get(relativeURL, new ClassReturnProcessor<T>(returnClass));
    }
    
    private <T> T put(String relativeURL, Object entity, ReturnProcessor<T> processor) {
        try {
            HttpPut put = getSimpleHttpFactory().newPut(getURL(relativeURL));
            
            String json = mapper.writeValueAsString(entity);
            
            put.setEntity(new StringEntity(json, ContentType.APPLICATION_JSON));
            
            return executeRequest(put, processor);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
    
    /**
     * Performs a PUT operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param entity The entity (DTO) to supply in the body of the PUT.
     * @param returnType The type that is expected to be returned.
     * @return The returned object, parsed into the specified returnType.
     */
    public <T> T put(String relativeURL, Object entity, TypeReference<T> returnType) {
        return put(relativeURL, entity, new TypeReferenceReturnProcessor<T>(returnType));
    }
  
    /**
     * Performs a PUT operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param entity The entity (DTO) to supply in the body of the PUT.
     * @param returnClass The class that is expected to be returned.
     * @return The returned object, parsed into the specified returnClass.
     */
    public <T> T put(String relativeURL, Object entity, Class<T> returnClass) {
        return put(relativeURL, entity, new ClassReturnProcessor<T>(returnClass));
    }
 
    /**
     * Implement this interface to perform a getPut operation.
     * 
     * @param <T> The type of object returned from the GET.
     */
    public interface ApplyChanges<T> {
        /**
         * Apply the changes.
         * @param input The input to transform.
         */
        void apply(T input);
    }
  
    private <GetType, PutType> PutType getPut(String relativeURL, 
            ApplyChanges<GetType> applyFunc,
            ReturnProcessor<GetType> getProcessor,
            ReturnProcessor<PutType> returnProcessor) {
    
        while (true) {
            try {
                GetType getObj = get(relativeURL, getProcessor);
                        
                applyFunc.apply(getObj);
               
                return put(relativeURL, getObj, returnProcessor);
            } catch (SimpleHTTPException e) {
                // Retry if HttpStatus.SC_CONFLICT (409)
                //
                if (e.getStatusCode() != HttpStatus.SC_CONFLICT) {
                    throw e;
                }
            }
        }
    }
   
    /**
     * Performs a get/apply/put operation, retrying if the server returns
     * an HTTP 409 Conflict message.
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents/{incId}").  
     * This is relative to the baseURL.
     * @param applyFunc Inteface used to apply the changes to the
     * object returned from the get.
     * @param getClass The class of the object returned from the get.
     * @param returnClass The class of the object returned from the put.
     * @return The object returned by the successful put.
     */
    public <GetType, PutType> PutType getPut(String relativeURL, 
            ApplyChanges<GetType> applyFunc, 
            Class<GetType> getClass,
            Class<PutType> returnClass) {
        
        return getPut(relativeURL, 
                applyFunc,
                new ClassReturnProcessor<GetType>(getClass),
                new ClassReturnProcessor<PutType>(returnClass));
    }
    
    /**
     * Performs a get/apply/put operation, retrying if the server returns
     * an HTTP 409 Conflict message.
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents/{incId}").  
     * This is relative to the baseURL.
     * @param applyFunc Inteface used to apply the changes to the
     * object returned from the get.
     * @param getType The TypeReference of the object returned from the get.
     * @param returnType The TypeReference of the object returned from the put.
     * @return The object returned by the successful put.
     */
    public <GetType, PutType> PutType getPut(String relativeURL, 
            ApplyChanges<GetType> applyFunc, 
            TypeReference<GetType> getTypeRef,
            TypeReference<PutType> returnTypeRef) {
        
        return getPut(relativeURL, 
                applyFunc,
                new TypeReferenceReturnProcessor<GetType>(getTypeRef),
                new TypeReferenceReturnProcessor<PutType>(returnTypeRef));
    }
    
    private <T> T delete(String relativeURL, ReturnProcessor<T> processor) {
        HttpDelete delete = getSimpleHttpFactory().newDelete(getURL(relativeURL));
        
        return executeRequest(delete, processor);
    }
    
    /**
     * Performs a DELETE operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param returnType The type that is expected to be returned.
     * @return The returned object, parsed into the specified returnType.
     */
    public <T> T delete(String relativeURL, TypeReference<T> returnType) {
        return delete(relativeURL, new TypeReferenceReturnProcessor<T>(returnType));
    }
   
    /**
     * Performs a DELETE operation on the specified relative URL.  This method expects a Content-type of
     * "application/json" to be returned from the server.
     * 
     * @param relativeURL The relative URL to GET (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param returnClass The type that is expected to be returned.
     * @return The returned object, parsed into the specified returnClass.
     */
    public <T> T delete(String relativeURL, Class<T> returnClass) {
        return delete(relativeURL, new ClassReturnProcessor<T>(returnClass));
    }
    
    private <T> T post(String relativeURL, Object entity, ReturnProcessor<T> processor) {
        try {
            HttpPost post = getSimpleHttpFactory().newPost(getURL(relativeURL));
            
            String json = mapper.writeValueAsString(entity);
            
            post.setEntity(new StringEntity(json, ContentType.APPLICATION_JSON));
            
            return executeRequest(post, processor);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
    
    /**
     * Performs a POST operation on the specified relative URL.  This method sends a Content-Type of "application/json"
     * and expects the same in return.
     * 
     * @param relativeURL The relative URL to POST to (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param entity The entity (DTO) to supply in the body of the POST.
     * @param returnType The type that is expected to be returned.
     * @return The object returned from the server, parsed into the specified returnType.
     */
    public <T> T post(String relativeURL, Object entity, TypeReference<T> returnType) {
        return post(relativeURL, entity, new TypeReferenceReturnProcessor<T>(returnType));
    }
  
    /**
     * Performs a POST operation on the specified relative URL.  This method sends a Content-Type of "application/json"
     * and expects the same in return.
     * 
     * @param relativeURL The relative URL to POST to (e.g. "/rest/orgs/{orgId}/incidents").  This is relative to the baseURL.
     * @param entity The entity (DTO) to supply in the body of the POST.
     * @param returnClass The type that is expected to be returned.
     * @return The object returned from the server, parsed into the specified returnClass.
     */
    public <T> T post(String relativeURL, Object entity, Class<T> returnClass) {
        return post(relativeURL, entity, new ClassReturnProcessor<T>(returnClass));
    }
  
    /**
     * Performs a GET on the specified relative URL and returns it as a string.  Note that it
     * is assumed that the returned data is in UTF-8 format (any charset that is returned
     * in the content type is currently ignored).
     * @param relativeURL The URL to get (relative to the baseURL).
     * @param contentTypeBuf A buffer where the returned content type will be stored (this
     * value can be null if you are not interested in the returned content type).
     * @return The data returned from the server as a string.
     */
    public String getContent(String relativeURL, StringBuffer contentTypeBuf) {
        HttpGet get = getSimpleHttpFactory().newGet(getURL(relativeURL));
        
        try {
            if (sessionInfo != null) {
                get.setHeader("X-sess-id", sessionInfo.getCsrfToken());
            }
           
            if (contextHeader != null) {
                get.setHeader("X-Co3ContextToken", contextHeader);
            }
            
            HttpResponse response = getHttpClient().execute(get);

            HttpEntity entity = readResponse(response, contentTypeBuf);
            
            return CharStreams.toString(new InputStreamReader(entity.getContent(), Charsets.UTF_8));
            
        } catch (IOException e) {
            throw new RuntimeException("Error while connecting", e);
        }
    }

    /**
     * Helper to create an Organization-specific URL for the org that the user is logged in to.
     * 
     * @param relativeURL The relative URL (e.g. a relative value of "/incidents" would return
     * "/rest/orgs/{orgId}/incidents").
     * 
     * @return The full URL for the user's org.  Note that this does NOT contain the baseURL, but
     * you can pass it directly to {@link #get(String, TypeReference)}, {@link #post(String, Object, TypeReference)}, etc.
     */
    public String getOrgURL(String relativeURL) {
        return String.format("/rest/orgs/%d%s", getOrgId(), relativeURL);
    }
    
    /**
     * Retrieve the user ID that the client was told of at the start of the session
     * @return the currently logged-in user's user ID
     */
    public Integer getUserID(){
        return sessionInfo.getUserId();
    }
   
    /**
     * Gets the server's constant data.  If it hasn't been loaded then it's loaded now.  This
     * result will be cached for subsequent calls.
     * @return The ConstDTO from the server.
     */
    public ConstDTO getConstData() {
        if (constData == null) {
            constData = get("/rest/const", new TypeReference<ConstDTO>(){});
        }
        
        return constData;
    }

    /**
     * Returns the const data as a Map.
     * @return A map that represents the const data.
     */
    public Map<String, Object> getConstDataAsMap() {
        return get("/rest/const", new TypeReference<Map<String, Object>>(){});
    }
    
    /**
     * Returns the org data as a Map.
     * @return A map that represents the org data.
     */
    public Map<String, Object> getOrgDataAsMap() {
        return get(getOrgURL(""), new TypeReference<Map<String, Object>>(){});
    }

    /**
     * Returns the org data as a FullOrgDTO object.
     * @return The org data.
     */
    public FullOrgDTO getOrgData() {
        return get(getOrgURL(""), new TypeReference<FullOrgDTO>(){});
    }
    
    /**
     * Internal method to authenticate to the server and load it's initial const data.
     */
    public void connect() {
        AuthenticationDTO auth = new AuthenticationDTO();
        
        auth.setEmail(email);
        auth.setPassword(password);
        
        sessionInfo = post("/rest/session", auth, new TypeReference<UserSessionDTO>(){});
    }
  
    /**
     * Gets the objectMapper that this client is using.
     */
    public ObjectMapper getObjectMapper() {
    	return mapper;
    }
    
    /**
     * Gets the ID of the org this object is working on.  This uses orgName to find the correct org.
     * @return The org ID.
     */
    private int getOrgId() {
        if (sessionInfo == null) {
            throw new IllegalStateException("connect must be called first");
        }
    
        List<SessionOrgInfoDTO> orgs = sessionInfo.getOrgs();
        List<Integer> candidates = Lists.newArrayList();
      
        if (orgs.isEmpty()) {
            throw new IllegalArgumentException("The user is not a member of any organizations.");
        }
       
        List<String> allOrgNames = new ArrayList<>();
        
        for (SessionOrgInfoDTO org : orgs) {
        	allOrgNames.add(org.getName());
        	
            if (org.getEnabled() && (orgName == null || org.getName().equalsIgnoreCase(orgName))) {
                candidates.add(org.getId());
            }
        }
       
        if (candidates.size() > 1) {
            throw new IllegalArgumentException(
            		String.format("Please specify the organization name to which you want to connect.  " +
            				"The user is a member of the following organizations:  %s", orgs));
        } else if (candidates.isEmpty()) {
            throw new IllegalArgumentException(String.format("The user is not a member of the specified organization '%s'.", orgName));
        }
        
        return candidates.get(0);
    }

    /**
     * Helper to read in an Apache HttpClient response object.
     * @param response The response returned from the GET/POST/PUT/DELETE method.
     * @param contentTypeBuf A buffer where the returned content type can be written.  This parameter
     * can be null if the caller doesn't care about the returned content type. 
     * @return The HttpEntity for the response.
     * @throws IllegalStateException If the HTTP code is not 200 (if the server reported a failure).
     */
    private HttpEntity readResponse(HttpResponse response, StringBuffer contentTypeBuf) {
        StatusLine status = response.getStatusLine();
        
        if (status.getStatusCode() != HttpStatus.SC_OK) {
            throw new SimpleHTTPException(status.getStatusCode(), status.toString());
        }
    
        Header contentType = response.getFirstHeader(HttpHeaders.CONTENT_TYPE);

        String contentTypeStr = contentType.getValue();
    
        if (contentTypeBuf != null) {
            contentTypeBuf.append(contentTypeStr);
        }
        
        final MediaType TEXT_HTML = MediaType.HTML_UTF_8.withoutParameters();
        final MediaType TEXT_PLAIN = MediaType.PLAIN_TEXT_UTF_8.withoutParameters();
        final MediaType APPLICATION_JSON = MediaType.JSON_UTF_8.withoutParameters();
        
        MediaType mediaType = MediaType.parse(contentTypeStr);
        
        if (mediaType.is(TEXT_HTML) || mediaType.is(TEXT_PLAIN)) {
            return response.getEntity();
        } else if (!mediaType.is(APPLICATION_JSON)) {
            throw new IllegalStateException(String.format("Expected %s content type; got %s", APPLICATION_JSON, contentType.getValue()));
        }
        
        return response.getEntity();
    }
    
    /**
     * Helper to convert a relative URL into an absolute URL (using the baseURL).
     * @param relativeURL The relative URL to convert.
     * @return
     */
    private URL getURL(String relativeURL) {
        try {
            URL url = new URL(baseURL, relativeURL);
            
            return url;
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }
    }
  
    /**
     * Helper interface to process the return InputStream and return an object
     * of a given type.
     *
     * @param <T> The type to return.
     */
    private interface ReturnProcessor<T> {
        T process(InputStream is) throws IOException;
    }
  
    /**
     * Helper to return T given TypeReference<T>
     *
     * @param <T> The type to return.
     */
    private class TypeReferenceReturnProcessor<T> implements ReturnProcessor<T> {
        private TypeReference<T> typeRef;
        
        private TypeReferenceReturnProcessor(TypeReference<T> typeRef) {
            this.typeRef = typeRef;
        }
        
        public T process(InputStream is) throws IOException {
            return mapper.readValue(is, typeRef);
        }
    }
   
    /**
     * Helper to return T given Class<T>
     * 
     * @param <T> The type to return.
     */
    private class ClassReturnProcessor<T> implements ReturnProcessor<T> {
        private Class<T> clazz;
        
        private ClassReturnProcessor(Class<T> clazz) {
            this.clazz = clazz;
        }
        
        public T process(InputStream is) throws IOException {
            return mapper.readValue(is, clazz);
        }
    }
    
    /**
     * Executes a HttpGet, HttpPut, HttpPost, etc. operation and returns an object of the
     * specified type.
     * @param req The request to execute.
     * @param returnProcessor An object to convert the InputStream to the specified type of object.
     * @return The object returned from the server, parsed into the specified type.
     */
    private <T> T executeRequest(HttpRequestBase req, ReturnProcessor<T> processor) {
        try {
            req.setHeader(HttpHeaders.CONTENT_TYPE, ContentType.APPLICATION_JSON.toString());
            
            if (sessionInfo != null) {
                req.setHeader("X-sess-id", sessionInfo.getCsrfToken());
            }
           
            if (contextHeader != null) {
                req.setHeader("X-Co3ContextToken", contextHeader);
            }
            HttpResponse response = getHttpClient().execute(req);
   
            HttpEntity entity = readResponse(response, null);
            
            try (InputStream is = entity.getContent()) {
                if (is == null) {
                    throw new IllegalStateException("Expected JSON response but didn't get any content");
                }
            
                return processor.process(is);
            }
        } catch (IOException e) {
            throw new RuntimeException("Error while connecting", e);
        }
    }
 
    /**
     * Gets the HttpClient object to use for this object.  If it hasn't been created already, then do so.
     */
    private HttpClient getHttpClient() {
        if (httpClient == null) {
            httpClient = getSimpleHttpFactory().newHttpClient();
        }
        return httpClient;
    }
   
    /**
     * Gets the SimpleHttpFactory to use for creating the Apache HTTP Client objects.  This concept 
     * exists to aid in unit testing.
     */
    SimpleHttpFactory getSimpleHttpFactory() {
        return new SimpleHttpFactory();
    }
}
