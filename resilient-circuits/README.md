# resilient-circuits
This package is a framework for rapid development of Resilient Action Module event processors in Python.

### Changelog

### Installation  
Instructions for building and installing this package can be found in the 
[repository README](https://github.com/ibmresilient/resilient-python-api/blob/master/README.md).


### Configuration

Configuration parameters for the server URLs, user credentials and so on
should be provided using a configuration file.  They can optionally also
be provided on the command-line.

If the environment variable `APP_CONFIG_FILE` is set, it defines the path
to your configuration file.  The default configuration file is named
`app.config` and is stored in ~/.resilient/app.config.

Generate a template app.config file with:
```
resilient-circuits config -c
```  

Or on Windows:
```
resilient-circuits.exe config -c
```

Edit the `app.config` file with parameters appropriate to your environment.__
Any sample components you are running may have additional sections that 
need to be added to the app.config file, which will be indicated in their README.  

### Running an example

After installing the resilient-circuits module, install a compatible integration
package or copy some sample component modules to your `components` directory.  
The path to this `components` directory will need to be specified in your app.config
file in the [resilient] section in the `componentsdir` parameter.  

Create a directory for resilient-circuits to write log files to and specify
its location in the `logdir` parameter in your app.config file.  

Once everything is configured, start the integration:
```
resilient-circuits run
```  

or on Windows,
```
resilient-circuits.exe run
```


### Logging

Script output is logged to a file "app.log", which rotates if it grows large.
On unix systems, the script output is also sent to syslog.
You should periodically check the log for warnings and errors.

### Usage:
```
resilient-circuits [-h] [-v]
                          {run,list,test,service,config,codegen,extract,customize,selftest,clone,ext:package,ext:convert}

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Print debug output

subcommands:
                        one of these options must be provided
    run                 Run the Resilient Circuits application
    list                List the installed Resilient Circuits components
    test                An interactive client for testing Resilient Circuits
                        messages
    service             Manage Resilient Circuits as a service
    config              Create or update a basic configuration file
    customize           Apply customizations to the Resilient platform
    selftest            Calls selftest functions for every package and prints
                        out their return states
    clone               Clone Resilient objects
```