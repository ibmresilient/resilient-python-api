# Resilient Circuits Python module.
This provides a convenient framework for Action Module applications.


### Requirements


The Resilient REST API is accessed by a helper module `co3` that should be
used for all Python client applications.  Install that package before you start.

Other requirements are installed when you install the package or setup.


__Installation__  
Instructions for building and installing this package can be found in the 
Python API README:  
[Python API README](../).


__Installation on Isolated Systems__  
To download all the dependencies so that they can be installed
onto an isolated machine, run this command from the top resilient-circuits directory:

    pip download --no-cache-dir --no-binary :all: .

This downloads various .tar.gz files that can each be copied to
your target machine and installed with 'pip install <file>.tar.gz'.


### Configuration

Configuration parameters for the server URLs, user credentials and so on
should be provided using a configuration file.  They can optionally also
be provided on the command-line.

If the environment variable `APP_CONFIG_FILE` is set, it defines the path
to your configuration file.  The default configuration file is named
`app.config` and is stored in ~/.resilient/app.config.

Generate a template app.config file with:  
`resilient-circuits config -c`

Or on Windows:  
`resilient-circuits.exe config -c`

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
`resilient-circuits run`  
`resilient-circuits.exe run`


### Logging

Script output is logged to a file "app.log", which rotates if it grows large.
On unix systems, the script output is also sent to syslog.
You should periodically check the log for warnings and errors.


## More Info

For more extensive integrations, including tasks, notes and artifacts or
for running resilient_circuits as a service,  
contact [success@resilientsystems.com](success@resilientsystems.com).
