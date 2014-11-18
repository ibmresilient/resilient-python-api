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
import java.io.FileInputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.apache.commons.cli.BasicParser;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.commons.lang.BooleanUtils;
import org.apache.commons.lang.StringUtils;

import com.google.common.collect.Lists;

/**
 * Represents common options for Co3 command line tools.
 */
public abstract class Co3Options {
    static final String CONFIG_FILE_ARG = "config";
    static final String BASE_URL_PROPERTY = "url";
    static final String EMAIL_PROPERTY = "email";
    static final String PASSWORD_PROPERTY = "password";
    static final String ORG_NAME_PROPERTY = "org";
    static final String SHORT_HELP_ARG = "h";
    static final String LONG_HELP_ARG = "help";
    
    static final String DEFAULT_BASE_URL = "https://app.co3sys.com/";
    static final String DEFAULT_CHARSET = "UTF-8";
    
    private Options options = new Options();
    private CommandLine commandLine;
    private Properties config = new Properties();
    private String commandLineSyntax;
    
    /**
     * @return The -url option or the default URL if -url wasn't specified.
     */
    public URL getBaseURL() {
        String url = getConfigValue(BASE_URL_PROPERTY, DEFAULT_BASE_URL);
        try {
            return new URL(url);
        } catch (MalformedURLException e) {
            throw new IllegalArgumentException(String.format("Invalid URL:  %s", url), e);
        }
    }

    /**
     * Helper interface for returning email and password with one call.
     */
    public interface PasswordInfo {
    	String getEmail();
    	String getPassword();
    }
    
    /**
     * Gets the email/password information needed for authentication.  If the values are not 
     * specified then the user is prompted.
     * 
     * Just to be explicit:  Calling this can result in a system console prompt.  To avoid 
     * the prompt, specify the arguments on the command line or in the config file.
     * @return The password information or null if the user cancelled.
     */
    public PasswordInfo getPasswordInfo() {
    	String email = getConfigValue(EMAIL_PROPERTY);
    	String password = getConfigValue(PASSWORD_PROPERTY);
    
    	while (StringUtils.isBlank(email)) {
    		System.console().printf("Enter e-mail address:  ");
    		email = System.console().readLine();
    	}
    
    	while (StringUtils.isBlank(password)) {
    		System.console().printf("Password:  ");
    		
    		password = new String(System.console().readPassword());
    	}
       
    	final String femail = email;
    	final String fpassword = password;
    	
        return new PasswordInfo() {
			@Override
			public String getEmail() {
				return femail;
			}

			@Override
			public String getPassword() {
				return fpassword;
			}
        };
    }
   
    /**
     * @return The -org option (or null if it is missing).
     */
    public String getOrgName() {
        return getConfigValue(ORG_NAME_PROPERTY);
    }
  
    /**
     * Add general options.  Subclasses should add their options in an addOptions implementation.
     * @param commandLineSyntax The command line syntax to include in the usage.
     */
    protected Co3Options(String commandLineSyntax) {
        this.commandLineSyntax = commandLineSyntax;
        
        options.addOption(CONFIG_FILE_ARG, true, "Configuration properties file name");
        options.addOption(SHORT_HELP_ARG, LONG_HELP_ARG, false, "Show help");

        options.addOption(BASE_URL_PROPERTY, true, String.format("The base URL to use (default is %s)", DEFAULT_BASE_URL));
        options.addOption(EMAIL_PROPERTY, true, "The email address to use");
        options.addOption(PASSWORD_PROPERTY, true, "The password to use");
        options.addOption(ORG_NAME_PROPERTY, true, "The organization to use (required if you are a member of multiple orgs)");
        
        addOptions(options);
    }

    /**
     * Helper to print command line usage and exit.  Note that this will call System.exit(0).
     */
    private void printUsage(PrintStream pw) {
        HelpFormatter formatter = new HelpFormatter();
        try(PrintWriter writer = new PrintWriter(pw)){

            formatter.printHelp(
                    writer,
                    HelpFormatter.DEFAULT_WIDTH,
                    commandLineSyntax,
                    null,
                    options,
                    HelpFormatter.DEFAULT_LEFT_PAD,
                    HelpFormatter.DEFAULT_DESC_PAD,
                    null);
            writer.flush();
        }
    
        System.exit(0);
    }
    
    /**
     * Helper to correct the user after receiving invalid input
     */
    protected void invalidArguments(String msg){
        System.err.println(msg);
        printUsage(System.err);
    }
    
    /**
     * Parses the specified arguments.
     * @param args The command line arguments.
     */
    public void parse(String [] args) {
        
        CommandLineParser parser = new BasicParser();

        try {
            commandLine = parser.parse(options, args);
        } catch (ParseException e) {
            throw new IllegalArgumentException("Invalid command line options", e);
        }
        
        if (hasConfigValue(SHORT_HELP_ARG) || hasConfigValue(LONG_HELP_ARG)) {
            printUsage(System.out);
        }
       
        config = loadConfigProps();
    }
    
    /**
     * Helper to create a name that can be used in a configuration file or system property.  Basically this just prepends
     * "co3." to the passed in name.
     * @param name The name.
     * @return "co3.<name>"
     */
    private static String makeConfigName(String name) {
        return String.format("co3.%s", name);
    }
   
    /**
     * Looks in the command line, system properties and configuration file for a particular configuration value.  Note
     * that name will be used to look on the command line, but "co3.<name>" will be used for system properties and
     * configuration properties.
     * @param name The name of the property.
     * @return The property value.
     */
    protected boolean hasConfigValue(String name) {
        if (commandLine != null && commandLine.hasOption(name)) {
            return true;
        }
      
        String configName = makeConfigName(name);
        
        if (BooleanUtils.toBoolean(System.getProperty(configName, "false"))) {
            return true;
        }
        
        return config != null && BooleanUtils.toBoolean(config.getProperty(configName, "false"));
    }
    
    /**
     * Looks in the command line, system properties and configuration file for a particular configuration value.  Note
     * that name will be used to look on the command line, but "co3.<name>" will be used for system properties and
     * configuration properties.
     * @param name The name of the property.
     * @return The property value.  null if the property could not be found.
     */
    protected String getConfigValue(String name) {
        return getConfigValue(name, null);
    }
   
    /**
     * Sets a configuration property.  Note that this is really only useful for testing.  Also, if a 
     * @param name
     * @param value
     */
    protected void setConfigValue(String name, String value) {
        if (commandLine != null && commandLine.hasOption(name)) {
            throw new IllegalArgumentException("Unable to override command line argument:  " + name);
        }
        
        config.setProperty(makeConfigName(name), value);
    }
    
    /**
     * Looks in the command line, system properties and configuration file for a particular configuration value.  Note
     * that name will be used to look on the command line, but "co3.<name>" will be used for system properties and
     * configuration properties.
     * @param defaultValue The value to return if the property cannot be found.
     * @return The property value.  Returns defaultValue if the property could not be found.
     */
    protected String getConfigValue(String name, String defaultValue) {
        // Order of preference:  Command line, then system property, then config file
        //
        String value = null;
        
        if (commandLine != null) {
            value = commandLine.getOptionValue(name);
        }
       
        String configName = makeConfigName(name);
        
        if (value == null) {
            value = System.getProperty(configName);
        }
        
        if (value == null && config != null) {
            value = config.getProperty(configName, defaultValue);
        }
        
        return value;
    }
    
    /**
     * Gets a map for the specified name.  Use this for command line arguments that are of the form:
     * <pre>
     *   -X key:value
     * </pre>
     * Note that these types of arguments can only be specified on the command line (not in a config
     * file).
     * @param name The name of the argument ("X" in the above example).
     * @return A map that represents the arguments.
     */
    protected Map<Object, Object> getConfigMap(String name) {
        return commandLine.getOptionProperties(name); 
    }
 
    /**
     * Gets a list of values for the specified name.  Use this for command line arguments that are 
     * of the form:
     * <pre>
     *   -arg val1 -arg val2 -arg val3
     * </pre>
     * Note that these types of arguments can only be specified on the command line (not in a config
     * file).
     * @param name The name of the argument ("arg" in the above example).
     * @return A list of arguments (["val1", "val2", val3"] in the above example).
     */
    protected List<String> getConfigList(String name) {
        if (commandLine.hasOption(name)) {
            return Lists.newArrayList(commandLine.getOptionValues(name));
        }
        
        return Lists.newArrayList();
    }
    
    /**
     * Retrieve any left-over non-recognized options and arguments.  For example:
     * <pre>
     *   program -url http://... -email fred@xyz.com -password password a b c d
     * </pre>
     * In the above example, ["a", "b", "c", "d"] will be returned.
     * Note that these types of arguments can only be specified on the command line (not in a config
     * file).
     * @return Left over non-recognized options and arguments.
     */
    protected List<String> getArgs() {
        return Lists.newArrayList(commandLine.getArgs());
    }
    
    /**
     * Loads the configuration properties file.
     * @param commandLine The command line object.
     * @return The configuration properties.
     * @throws IOException If there's an exception reading the file.
     */
    private Properties loadConfigProps() {
        Properties configProps = new Properties();
       
        String configFileName = commandLine.getOptionValue(CONFIG_FILE_ARG);
       
        if (configFileName == null) {
        	return configProps;
        }
        
        File configFile = new File(configFileName);
       
        if (!configFile.exists()) {
            return configProps;
        }
     
        try {
            try (FileInputStream configStream = new FileInputStream(configFile)) {
                configProps.load(configStream);
            }
        } catch (IOException e) {
            throw new IllegalArgumentException("Invalid configuration file", e);
        }
        
        return configProps;
    }
    
    /**
     * Subclasses must implement this to add their own command line options.
     * @param options Add to this object using options.addOption(...).
     */
    protected abstract void addOptions(Options opt);
}
