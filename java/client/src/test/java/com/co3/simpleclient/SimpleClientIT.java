package com.co3.simpleclient;

import static org.junit.Assert.*;

import java.io.IOException;
import java.net.MalformedURLException;

import org.junit.Before;
import org.junit.Test;

import com.co3.dto.json.ConstDTO;

public class SimpleClientIT {
	private ServerConfig config;
	
	@Before
	public void setup() throws IOException {
		config = ServerConfig.load("itconfig.json");
	}
	
	@Test
	public void testConnect() throws MalformedURLException {
		SimpleClient sc = new SimpleClient(config);
		
		ConstDTO constData = sc.getConstData();
		
		assertNotNull(constData);
	}
}
