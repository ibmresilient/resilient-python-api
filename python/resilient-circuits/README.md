
### Python setup

The Resilient REST API is accessed by a helper module 'co3' that should be
used for all Python client applications.  Install this module before you start.

To build the package, from the main directory run this command
```
python setup.py bdist_wheel --universal
```
This creates a wheel file and puts in in a dist directory.
dist/resilient_circuits-24.0.1-py2.py3-none-any.whl

To install the package, run this command
```
pip install resilient_circuits-24.0.1-py2.py3-none-any.whl
```

## Configuration

Configuration parameters for the server URLs, user credentials and so on
should be provided using a configuration file.  They can optionally also
be provided on the command-line.  This package includes a configuration
file template, which should be copied and edited for your environment.

If the environment variable `APP_CONFIG_FILE` is set, it defines the path
to your configuration file.  The default configuration file is named `app.config`.

Your project should be structured as follows:
```
project/
├── app.config
├── components
│   ├── my_custom_component.py
├── lib
│   ├── helper_module1.py
│   ├── helper_module2.py
├── templates
|.. ├── template_file.jinja 
├── run.py
```

## Running the example integration

After installing the resilient-circuits package, copy the provided components, lib, and scripts directories and also the run.py and app.config files.
Edit the `app.config` file with parameters appropriate to your environment.
Then run the action script:

    python run.py
    

### Logging

Script output is logged to a file "app.log", which rotates if it grows large.
On unix systems, the script output is also sent to syslog.
You should periodically check the log for warnings and errors.


## More Info

For more extensive integrations, including tasks, notes and artifacts,
contact [success@resilientsystems.com](success@resilientsystems.com).
