## Resilient SimpleClient Python module
Used to interact with Resilient REST API


__Installation__  
Instructions for building and installing this package can be found in the 
Python API README:  
[Python API README](../).


__Installation on Isolated Systems__  
To download all the dependencies so that they can be installed
onto an isolated machine, run this command from the top co3 directory:

    pip download --no-cache-dir --no-binary :all: .

This downloads various .tar.gz files that can each be copied to
your target machine and installed with 'pip install <file>.tar.gz'.

__To test the package:__  
   python setup.py test [-a "<optional co3argparse args>"] [-c <config file>] [-p "<optional pytest args>"]  
   e.g. `python setup.py test -a "--org=Test" -c ~/my.config -p "-s"`
   

## Command Line Utilities
The co3 package includes several useful command line tools to help with testing and configuration.

|Utility|Description|Usage|
| --- | --- | --- |
|finfo|Read and display metadata about the fields in your Resilient org.  [View Detailed Description](../examples/rest/finfo)|finfo --help|
|gadget|General purpose command line access to Resilient REST API.  [View Detailed Description](../examples/rest/gadget)|gadget --help|
|res-keyring|Uses Python keyring to create/store secure values for the specially marked parameters in your config file.  It reads your app.config file, either from ~/.resilient/app.config or from $APP\_CONFIG\_FILE.  All keys that have a value starting with '^' are pulled and you will be prompted for a value to store for that key.  These values are stored in your operating system's secure credentials management system.  This feature is not available when co3 is installed directly on the Resilient appliance due to lack of availability of a compatible backend for keyring.|res-keyring|
