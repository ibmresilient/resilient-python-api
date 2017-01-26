This package is a py.test plugin that provides fixtures to fascilitate testing resilient-circuits applications


Requirements
============

The `co3` and `resilient-circuits` packages should be installed before use.

Other requirements are installed when you install the package.


Installing this module
======================

To install a pre-built package file:

    pip install dist/pytest_resilient_circuits-x.x.x.tar.gz


To install directly into your local Python environment:

    python setup.py install


To build the installable package file:

    python setup.py sdist --formats=gztar

This creates a single file `dist/pytest_resilient_circuits-x.x.x.tar.gz` (the filename will
vary according to the current version of this repository).


Included Fixtures
=================
Once the plugin is installed via setup or pip, it will make the following fixtures available in pytest:

__circuits\_app__: This will start up resilient-circuits with the specified appliance and credentials. Your test module should have a variable "base_dir" that contains the path to your project directory.  The appliance location and credentials will be pulled from the following environment variables:

- RESILIENT_APPLIANCE
- RESILIENT_ORG
- RESILIENT_USER
- RESILIENT_PASSWORD

This is a "class" scoped fixture, so will be run once per class of tests. It will automatically load any components from the "components" directory in the directory specified by "base_dir"

__configure_resilient__: This will clear out all existing configuration items from the org and then create any ones required for your tests. This is a "class" scoped fixture, so the configuration will be run once for a class of tests. Class members should be set as follows to describe required configuration elements. Any that aren't necessary can be excluded.

- destinations = ("<destination1 name>", "<destination2 name>", ...)
- action_fields = {"<programmatic_name>": ("<select, number, text, etc...>", "<display_name>"),
                   "<programmatic_name>": ("<select, number, text, etc...>", "<display_name>"), ...}
- custom_fields = {"<programmatic_name>": ("<select, number, text, etc...>", "<display_name>"),
                   "<programmatic_name>": ("<select, number, text, etc...>", "<display_name>"), ...}
- automatic_actions = {"<display_name>": ("<destination name>", "<Incident, Artifact, Task, etc>", (condition1, condition2, etc)),
                       "<display_name>": ("<destination name>", "<Incident, Artifact, Task, etc>", (condition1, condition2, etc))}
                       *note that conditions are a dict in ConditionDTO format
- manual_actions ={"<display_name>": ("<destination name>", "<Incident, Artifact, Task, etc>", ("<action field1>", "<action field2>", ...)),
                   "<display_name>": ("<destination name>", "<Incident, Artifact, Task, etc>", ("<action field1>", "<action field2>", ...))} 
                   
__new_incident__: This will create a new incident in Resilient for the test to use. This is a "function" scoped fixture, so you can get a fresh incident for each test.



More Info
=========
For more information,
contact [success@resilientsystems.com](success@resilientsystems.com).
