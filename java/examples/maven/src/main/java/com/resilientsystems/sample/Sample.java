package com.resilientsystems.sample;

import com.co3.dto.incident.json.PartialIncidentDTO;
import com.co3.simpleclient.ServerConfig;
import com.co3.simpleclient.SimpleClient;
import com.fasterxml.jackson.core.type.TypeReference;

import java.io.File;
import java.io.IOException;
import java.util.List;

/**
 * Minimal command line sample using the Resilient Java API.
 */
public class Sample {
    /**
     * The Jackson TypeReference to use for getting incidents.  This allow us to use type-safe returns from the API.
     */
    private static final TypeReference<List<PartialIncidentDTO>> INC_LIST_TYPE = new TypeReference<List<PartialIncidentDTO>>() {};

    private static final String CONFIG_FILE_NAME = "config.json";

    public static void main(String [] args) throws IOException {
        // Load the configuration file.
        ServerConfig serverConfig = ServerConfig.load(new File(CONFIG_FILE_NAME));

        checkRequiredConfig(serverConfig);

        // Password not included in file, read it in.
        if (serverConfig.getPassword() == null) {
            String password = new String(System.console().readPassword("Password: "));

            serverConfig.setPassword(password);
        }

        SimpleClient simpleClient = new SimpleClient(serverConfig);

        simpleClient.connect();

        List<PartialIncidentDTO> incidents = simpleClient.get("incidents?return_level=partial", INC_LIST_TYPE);

        for (PartialIncidentDTO incident : incidents) {
            System.out.printf("%d:  %s\n", incident.getId(), incident.getName());
        }
    }

    private static void checkRequiredConfig(ServerConfig serverConfig) {
        // User is required.
        if (serverConfig.getUser() == null) {
            throw newParameterException("user");
        } else if (serverConfig.getRestUrl() == null) {
            throw newParameterException("restUrl");
        }
    }

    private static IllegalArgumentException newParameterException(String name) {
        return new IllegalArgumentException(String.format("%s required in configuration file %s", name, CONFIG_FILE_NAME));
    }
}

