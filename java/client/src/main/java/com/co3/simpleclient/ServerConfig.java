package com.co3.simpleclient;

import java.io.File;
import java.io.IOException;

import org.apache.commons.lang.text.StrSubstitutor;
import org.codehaus.jackson.map.ObjectMapper;

/**
 * Simple bean class that holds the configuration needed to connect to a Co3 server.
 */
public class ServerConfig {
	private static ObjectMapper mapper = new ObjectMapper();
	
	private String user = null;
	private String password = null;
	private String orgName = null;
	private String trustStore = null;
	private String trustStorePassword = null;
	private String jmsUrl = null;
	private String restUrl = null;
	
	public static File getDefaultConfigDir() {
		return new File(System.getProperty("user.home"), "co3");
	}
	
	public static ServerConfig load(File file) throws IOException {
		synchronized (mapper) {
			return mapper.readValue(file, ServerConfig.class);
		}
	}
	
	public static ServerConfig load(String relativeFileName) throws IOException {
		return load(new File(getDefaultConfigDir(), relativeFileName));
	}
	public String getUser() {
		return user;
	}
	public void setUser(String user) {
		this.user = user;
	}
	public String getPassword() {
		return password;
	}
	public void setPassword(String password) {
		this.password = password;
	}
	public String getOrgName() {
		return orgName;
	}
	public void setOrgName(String orgName) {
		this.orgName = orgName;
	}
	public String getTrustStore() {
		return trustStore == null ? null : StrSubstitutor.replaceSystemProperties(trustStore);
	}
	public void setTrustStore(String trustStore) {
		this.trustStore = trustStore;
	}
	public String getTrustStorePassword() {
		return trustStorePassword;
	}
	public void setTrustStorePassword(String trustStorePassword) {
		this.trustStorePassword = trustStorePassword;
	}
	public String getJmsUrl() {
		return jmsUrl;
	}
	public void setJmsUrl(String jmsUrl) {
		this.jmsUrl = jmsUrl;
	}
	public String getRestUrl() {
		return restUrl;
	}
	public void setRestUrl(String restUrl) {
		this.restUrl = restUrl;
	}
}
