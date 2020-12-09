#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Command line tool to manage and run resilient-circuits """
from __future__ import absolute_import

import argparse
import logging
import os
import os.path
import sys
from collections import defaultdict
import pkg_resources
import resilient
import datetime
import time
import uuid
from resilient import ensure_unicode, get_config_file
from resilient_circuits.app import AppArgumentParser
from resilient_circuits.util.resilient_codegen import codegen_functions, codegen_package, codegen_reload_package, print_codegen_reload_commandline, extract_to_res
from resilient_circuits.util.resilient_customize import customize_resilient
from resilient_circuits.util.resilient_ext import ext_command_handler

# What code will be used if any apps tests fail when running resilient-circuits 'selftest'
SELFTEST_FAILURE_EXIT_CODE = 1

# Deprecation messages
DEPRECATION_MSG_CLONE = """\nDEPRECATING: We are deprecating the 'clone' command in resilient-circuits.
This functionality has been moved to the resilient-sdk tool.\n"""

if sys.version_info.major == 2:
    from io import open
else:
    unicode = str
try:
    # For all python < 3.2
    import backports.configparser as configparser
except ImportError:
    import configparser

try:
    from builtins import input
except ImportError:
    # Python 2
    from __builtin__ import raw_input as input

LOG = logging.getLogger("resilient_circuits_cmd_logger")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())


def windows_service(service_args, res_circuits_args):
    """Register a windows service"""
    try:
        import win32serviceutil
        from resilient_circuits.bin import service_wrapper

        if res_circuits_args:
            # Set the command line arguments to pass to "resilient-circuits.exe run"
            service_wrapper.irms_svc.setResilientArgs(res_circuits_args)

        sys.argv = sys.argv[0:1] + service_args
        win32serviceutil.HandleCommandLine(service_wrapper.irms_svc)
    except ImportError:
        LOG.error("Requires PYWIN32 Package. Please download and install from: "
                  "https://sourceforge.net/projects/pywin32/files/pywin32/")


def supervisor_service():
    """Register a unix service with supervisord [deprecated]"""
    pass


def manage_service(service_args, res_circuits_args):
    """Register a windows or unix service"""
    if os.name == 'nt':
        windows_service(service_args, res_circuits_args)
    else:
        LOG.error("Not implemented")
        # supervisor_service(service_args, res_circuits_args)


def run(resilient_circuits_args, restartable=False, config_file=None):
    """Run resilient-circuits"""
    # Leave only the arguments for the run command
    if restartable:
        # import here b/c it is slow
        from resilient_circuits import app_restartable as app
    else:
        from resilient_circuits import app
    sys.argv = sys.argv[0:1] + resilient_circuits_args
    kwargs = {}
    if config_file:
        kwargs = {"config_file": config_file}
    app.run(**kwargs)


def list_installed(args):
    """print list of installed packages with their components"""
    LOG.debug("resilient-circuits.list")
    components = defaultdict(list)
    # Resilient packages can have several entry-points,
    # - resilient.circuits.config: produces default configuration sections
    # - resilient.circuits.customize: produces schema customizations
    # - resilient.circuits.components: identifies components that implement actions, functions, etc.
    # We want to list all components, but include (as "empty") packages that define the other entry-points too.
    entry_points = []
    entry_points.extend([ep for ep in pkg_resources.iter_entry_points('resilient.circuits.config')])
    entry_points.extend([ep for ep in pkg_resources.iter_entry_points('resilient.circuits.customize')])
    component_entry_points = [ep for ep in pkg_resources.iter_entry_points('resilient.circuits.components')]
    entry_points.extend(component_entry_points)
    LOG.debug(u"Found %d installed entry-points", len(entry_points))
    for ep in entry_points:
        components[ep.dist].append(ep)
    if not components:
        LOG.info(u"No resilient-circuits components are installed")
        return

    ep_list = {}
    LOG.info(u"The following packages and components are installed:")
    for dist, component_list in components.items():
        if args.verbose:
            clist = "\n\t".join([str(ep) for ep in component_list if ep in component_entry_points])
            if clist == "":
                ep = u"{} ({}):\n\t(Package does not define any components)".format(
                    dist.as_requirement(),
                    dist.egg_info)
            else:
                ep = u"{} ({}):\n\t{}".format(
                    dist.as_requirement(),
                    dist.egg_info,
                    clist)
        else:
            clist = "\n\t".join([ep.name for ep in component_list if ep in component_entry_points])
            if clist == "":
                ep = u"{}:\n\t(Package does not define any components)".format(
                    dist.as_requirement())
            else:
                ep = u"{}:\n\t{}".format(
                    dist.as_requirement(),
                    clist)

        ep_list[str(dist.as_requirement())] = ep

    for ep_item in sorted(ep_list.keys()):
        LOG.info(ep_list[ep_item])


def generate_default(install_list):
    """ return string containing entire default app.config """
    base_config_fn = pkg_resources.resource_filename("resilient_circuits", "data/app.config.base")
    entry_points = pkg_resources.iter_entry_points('resilient.circuits.configsection')
    additional_sections = []
    remaining_list = install_list[:] if install_list else []
    for entry in entry_points:
        dist = entry.dist
        package_name = entry.dist.project_name

        # if a list is provided, use it to filter which packages to add to the app.config file
        if install_list is not None and package_name not in remaining_list:
            LOG.debug("{} bypassed".format(package_name))
            continue
        elif package_name in remaining_list:
            remaining_list.remove(package_name)

        try:
            func = entry.load()
        except ImportError:
            LOG.exception(u"Failed to load configuration defaults for package '%s'", repr(dist))
            continue

        new_section = None
        try:
            config_data = func()
            if config_data:
                required_config = configparser.ConfigParser(interpolation=None)
                LOG.debug(u"Config Data String:\n%s", config_data)
                required_config.read_string(unicode(config_data))
                new_section = required_config.sections()[0]
        except:
            LOG.exception(u"Failed to get configuration defaults for package '%s'", repr(dist))
            continue

        if new_section:
            additional_sections.append(config_data)

    LOG.debug("Found %d sections to generate", len(additional_sections))

    if install_list and len(remaining_list) > 0:
        LOG.warning("%s not found. Check package name(s)", remaining_list)

    with open(base_config_fn, 'r') as base_config_file:
        base_config = base_config_file.read()
        return "\n\n".join(([base_config, ] + additional_sections))

def generate_or_update_config(args):
    """ Create or update config file based on installed components.

    :param args: Command-line args for Resilient circuits 'config' sub-command.
    """
    usage_type = "CREATING" if args.create else "UPDATING"
    # Get the config file name.
    config_filename = get_config_file(filename=args.filename, generate_filename=True)

    file_exists = os.path.exists(config_filename)

    if file_exists:
        if args.create:
            choice = ""
            while choice not in ('y', 'n'):
                choice = input(u"%s exists. Do you want to overwrite? (y/n): " % config_filename)
            if choice == 'n':
                LOG.error(u"Config file creation cancelled.")
                return
    elif args.update:
        LOG.error(u"File %s does not exist. Update cancelled.", config_filename)
        return

    LOG.info(u"%s config file %s", usage_type, config_filename)

    if args.create:
        # Write out default file
        with open(config_filename, "w+", encoding="utf-8") as config_file:
            config_file.write(generate_default(args.install_list))
            LOG.info(u"Configuration file generated: %s", config_filename)
            LOG.info(u"Please manually edit with your specific configuration values.")

    else:
        # Update existing file
        config = configparser.ConfigParser(interpolation=None)
        updated = False
        with open(config_filename, "r", encoding="utf-8") as config_file:
            first_byte = config_file.read(1)
            if first_byte != u'\ufeff':
                # Not a BOM, no need to skip first byte
                config_file.seek(0)
            config.read_file(config_file)
            existing_sections = config.sections()

        entry_points = pkg_resources.iter_entry_points('resilient.circuits.configsection')
        remaining_list = args.install_list[:] if args.install_list else []

        with open(config_filename, "a", encoding="utf-8") as config_file:
            for entry in entry_points:
                dist = entry.dist
                package_name = entry.dist.project_name
                try:
                    func = entry.load()
                except ImportError:
                    LOG.exception(u"Failed to load configuration defaults for package '%s'", repr(dist))
                    continue

                new_section = None
                try:
                    config_data = func()
                    if config_data:
                        required_config = configparser.ConfigParser(interpolation=None)
                        LOG.debug(u"Config Data String:\n%s", config_data)
                        required_config.read_string(unicode(config_data))
                        new_section = required_config.sections()[0]
                except:
                    LOG.exception(u"Failed to get configuration defaults for package '%s'", repr(dist))
                    continue

                LOG.debug(u"Required Section: %s", new_section)
                if new_section and new_section not in existing_sections:
                    if args.install_list is None or package_name in remaining_list:
                        # Add the default data for this required section to the config file
                        LOG.info(u"Adding new section '%s' for '%s'", new_section, dist)
                        if package_name in remaining_list:
                            remaining_list.remove(package_name)

                        config_file.write(u"\n" + config_data)
                        updated = True
                else:
                    LOG.debug(u"Section '%s' already present, not adding", new_section)
                    LOG.debug(u"%s %s", new_section, package_name)
                    if package_name in remaining_list:
                        remaining_list.remove(package_name)

            if args.install_list and len(remaining_list) > 0:
                LOG.warning("%s not found. Check package name(s)", remaining_list)

            if updated:
                LOG.info(u"Update finished.  "
                         u"New sections may require manual edits with your specific configuration values.")
            else:
                LOG.info(u"No updates.")


def generate_code(args):
    """generate template code components from functions"""
    parser = AppArgumentParser(config_file=resilient.get_config_file())
    (opts, extra) = parser.parse_known_args()
    client = resilient.get_client(opts)

    if args.cmd == "extract" and args.output:
        extract_to_res(client, args.exportfile,
                          args.messagedestination, args.function, args.workflow, args.rule,
                          args.field, args.datatable, args.task, args.script, args.artifacttype,
                          args.output, args.zip)
    elif args.reload:
        codegen_reload_package(client, args)
    elif args.package:
        # codegen an installable package
        output_base = os.path.join(os.curdir, args.package)
        codegen_package(client, args.exportfile, args.package,
                        args.messagedestination, args.function, args.workflow, args.rule,
                        args.field, args.datatable, args.task, args.script, args.artifacttype,
                        os.path.expanduser(output_base))
    elif args.function:
        # codegen a component for one or more functions
        if len(args.function) > 1:
            default_name = "functions.py"
        else:
            default_name = "{}.py".format(args.function[0])
        output_dir = os.path.expanduser(opts["componentsdir"] or os.curdir)
        output_file = args.output or default_name
        if not output_file.endswith(".py"):
            output_file = output_file + ".py"
        codegen_functions(client, args.exportfile, args.function, args.workflow, args.rule, args.artifacttype,
                          output_dir, output_file)

def selftest(args):
    """loop through every selftest for every eligible package, call and store returned state,
        print out package and their selftest states"""

    components = defaultdict(list)

    # custom entry_point only for selftest functions
    selftest_entry_points = [ep for ep in pkg_resources.iter_entry_points('resilient.circuits.selftest')]
    for ep in selftest_entry_points:
        components[ep.dist].append(ep)

    if len(selftest_entry_points) == 0:
        LOG.info("No selftest entry points found.")
        return None

    # Generate opts array necessary for ResilientComponent instantiation
    opts = AppArgumentParser(config_file=resilient.get_config_file()).parse_args("", None);

    # make a copy
    install_list = list(args.install_list) if args.install_list else []

    # Prepare a count of exceptions found with selftests.
    selftest_failure_count = 0

    for dist, component_list in components.items():
        if args.install_list is None or dist.project_name in install_list:
            # remove name from list
            if dist.project_name in install_list:
                install_list.remove(dist.project_name)

            # add an entry for the package
            LOG.info("%s: ", dist.project_name)
            for ep in component_list:
                # load the entry point
                f_selftest = ep.load()

                try:
                    # f_selftest is the selftest function, we pass the selftest resilient options in case it wants to use it
                    start_time_milliseconds = int(round(time.time() * 1000))

                    status = f_selftest(opts)

                    end_time_milliseconds = int(round(time.time() * 1000))

                    delta_milliseconds = end_time_milliseconds - start_time_milliseconds
                    delta_seconds = delta_milliseconds / 1000

                    state = status.get("state")

                    if isinstance(state, str):
                        LOG.info("\t%s: %s\n\tselftest output:\n\t%s\n\tElapsed time: %f seconds", ep.name, state, status, delta_seconds)

                        if state.lower() == "failure":
                            selftest_failure_count += 1

                    else:
                        LOG.info("\t%s:\n\tUnsupported dictionary returned:\n\t%s\n\tElapsed time: %f seconds", ep.name, status, delta_seconds)

                except Exception as e:
                    LOG.error("Error while calling %s. Exception: %s", ep.name, str(e))
                    selftest_failure_count += 1
                    continue

    # any missed packages?
    if len(install_list):
        LOG.warning("%s not found. Check package name(s)", install_list)

    # Check if any failures were found and printed to the console
    if selftest_failure_count:
        sys.exit(SELFTEST_FAILURE_EXIT_CODE)


def find_workflow_by_programmatic_name(workflows, pname):
    for workflow in workflows:
        if workflow.get("programmatic_name") == pname:
            return workflow

    return None


def clone(args):
    parser = AppArgumentParser(config_file=resilient.get_config_file())
    (opts, extra) = parser.parse_known_args()
    latest_export_uri = "/configurations/exports/"

    client = resilient.get_client(opts)

    # Generate + get latest export from Resilient Server
    export_data = client.post(latest_export_uri, {"layouts": True, "actions": True, "phases_and_tasks": True})

    # Get the export date.
    last_date = export_data["export_date"]

    dt = datetime.datetime.utcfromtimestamp(last_date / 1000.0)
    LOG.info(u"Clone is based on the organization export from {}.".format(dt))

    new_export_data = export_data.copy()
    whitelist_dict_keys = ["incident_types", "fields"]  # Mandatory keys
    for dict_key in new_export_data:
        if dict_key not in whitelist_dict_keys and type(new_export_data[dict_key]) is list:
            new_export_data[dict_key] = []  # clear the new export data, the stuff we clear isn't necessary for cloning

    workflow_names = args.workflow  # names of workflow a (target) and b (new workflow)
    if workflow_names:  # if we're importing workflows
        if len(workflow_names) != 2:
            raise Exception("Only specify the original workflow api name and a new workflow api name")

        # Check that 'workflows' are available (v28 onward)
        workflow_defs = export_data.get("workflows")
        if workflow_defs is None:
            raise Exception("Export does not contain workflows")

        original_workflow_api_name = workflow_names[0]
        new_workflow_api_name = workflow_names[1]

        duplicate_check = find_workflow_by_programmatic_name(workflow_defs, new_workflow_api_name)
        if duplicate_check is not None:
            raise Exception("Workflow with the api name {} already exists".format(new_workflow_api_name))

        original_workflow = find_workflow_by_programmatic_name(workflow_defs, original_workflow_api_name)
        if original_workflow is None:
            raise Exception("Could not find original workflow {}".format(original_workflow_api_name))

        # This section just fills out the stuff we need to replace to duplicate
        new_workflow = original_workflow.copy()
        # Random UUID, not guaranteed to not collide but is extremely extremely extremely unlikely to collide
        new_workflow["uuid"] = str(uuid.uuid4())
        new_workflow["programmatic_name"] = new_workflow_api_name
        new_workflow["export_key"] = new_workflow_api_name
        old_workflow_name = new_workflow["name"]
        new_workflow["name"] = new_workflow_api_name
        new_workflow["content"]["workflow_id"] = new_workflow_api_name
        new_workflow["content"]["xml"] = new_workflow["content"]["xml"].replace(original_workflow_api_name,
                                                                                new_workflow_api_name)
        new_workflow["content"]["xml"] = new_workflow["content"]["xml"].replace(old_workflow_name,
                                                                                new_workflow_api_name)

        new_export_data["workflows"] = [new_workflow]

    uri = "/configurations/imports"
    result = client.post(uri, new_export_data)
    import_id = result["id"]  # if this isn't here and the response code is 200 OK, something went really wrong

    if result["status"] == "PENDING":
        result["status"] = "ACCEPTED"      # Have to confirm changes
        uri = "/configurations/imports/{}".format(import_id)
        client.put(uri, result)
        LOG.info("Imported successfully")
    else:
        raise Exception("Could not import because the server did not return an import ID")

def add_ext_arguments(cmd, ext_parser):
    """Add arguments to the given ext: command"""

    # Add cmd specific arguments
    if cmd == "ext:package":
        ext_parser.add_argument("-p",
            help="Path to the directory containing the setup.py file",
            default=os.getcwd(),
            required=True,
            metavar="path")

        ext_parser.add_argument("--keep-build-dir",
            help="Do not delete the dist/build directory",
            action="store_true")

    elif cmd == "ext:convert":
        ext_parser.add_argument("-p",
            help="Path to the (old) Integration that can be in .tar.gz or .zip format",
            required=True,
            metavar="path")

    # Add common (optional) arguments
    if cmd in ("ext:package", "ext:convert"):

        ext_parser.add_argument("--display-name",
            help="The Display Name to give the Extension",
            nargs="?",
            metavar="name")

    return ext_parser

def main():
    """Main commandline"""
    # create base parser for extract and codgen
    common_parser = argparse.ArgumentParser(add_help=False)

    """
    # Options for 'codegen'
    common_parser.add_argument("-f", "--function",
                                type=ensure_unicode,
                                help="Generate code for the specified function(s)",
                                nargs="*")
    common_parser.add_argument("-m", "--messagedestination",
                                type=ensure_unicode,
                                help="Generate code for all functions that use the specified message destination(s)",
                                nargs="*")
    common_parser.add_argument("--workflow",
                                type=ensure_unicode,
                                help="Include customization data for workflow(s)",
                                nargs="*")
    common_parser.add_argument("--rule",
                                type=ensure_unicode,
                                help="Include customization data for rule(s)",
                                nargs="*")
    common_parser.add_argument("--field",
                                type=ensure_unicode,
                                help="Include customization data for incident field(s)",
                                nargs="*")
    common_parser.add_argument("--datatable",
                                type=ensure_unicode,
                                help="Include customization data for datatable(s)",
                                nargs="*")
    common_parser.add_argument("--task",
                                type=ensure_unicode,
                                help="Include customization data for automatic task(s)",
                                nargs="*")
    common_parser.add_argument("--script",
                                type=ensure_unicode,
                                help="Include customization data for script(s)",
                                nargs="*")
    common_parser.add_argument("--artifacttype",
                               type=ensure_unicode,
                               help="Include customization data for artifact types(s)",
                               nargs="*")
    common_parser.add_argument("--exportfile",
                                type=ensure_unicode,
                                help="Generate based on organization export file (.res)")
    common_parser.add_argument("-o", "--output",
                                type=ensure_unicode,
                                help="Output file name")
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Print debug output", action="store_true")

    subparsers = parser.add_subparsers(title="subcommands",
                                       help="one of these options must be provided",
                                       description="valid subcommands",
                                       dest="cmd")
    subparsers.required = True

    run_parser = subparsers.add_parser("run",
                                       help="Run the Resilient Circuits application")
    list_parser = subparsers.add_parser("list",
                                        help="List the installed Resilient Circuits components")
    test_parser = subparsers.add_parser("test",
                                        help="An interactive client for testing Resilient Circuits messages")
    service_parser = subparsers.add_parser("service",
                                           help="Manage Resilient Circuits as a service")
    config_parser = subparsers.add_parser("config",
                                          help="Create or update a basic configuration file")
    codegen_parser = subparsers.add_parser("codegen", parents=[common_parser],
                                           help="Deprecated for resilient-circuits, functionality moved to the resilient-sdk tool",
                                           )
    extractfile_parser = subparsers.add_parser("extract", parents=[common_parser],
                                                help="Deprecated for resilient-circuits, functionality moved to the resilient-sdk tool")
    customize_parser = subparsers.add_parser("customize",
                                             help="Apply customizations to the Resilient platform")
    selftest_parser = subparsers.add_parser("selftest",
                                        help="Calls selftest functions for every package and prints out their return states")
    clone_parser = subparsers.add_parser("clone",
                                         help="Deprecated for resilient-circuits, functionality moved to the resilient-sdk tool",
                                         description="Deprecated for resilient-circuits, functionality moved to the resilient-sdk tool")
    '''Commenting out ext commands until future release
    # Add parser for ext:package
    # Usage 1: resilient-circuits ext:package <<path_to_package>>
    # Usage 2: resilient-circuits ext:package --display_name "My New Extension" <<path_to_package>>
    ext_package_help_msg = "Package an Integration into a Resilient Extension"
    ext_package_parser = subparsers.add_parser("ext:package",
                                        usage="%(prog)s -p <<path_to_package>>",
                                        help=ext_package_help_msg,
                                        description=ext_package_help_msg,
                                        argument_default=argparse.SUPPRESS)

    ext_package_parser = add_ext_arguments("ext:package", ext_package_parser)

    # Add parser for ext:convert
    # Usage: resilient-circuits ext:convert <<path_to_built_distribution>>
    ext_convert_help_msg = "Convert an old (built) Integration that can be in .tar.gz or .zip format into a Resilient Extension"
    ext_convert_parser = subparsers.add_parser("ext:convert",
                                        usage="%(prog)s -p <<path_to_built_distribution>>",
                                        help=ext_convert_help_msg,
                                        description=ext_convert_help_msg,
                                        argument_default=argparse.SUPPRESS)

    ext_convert_parser = add_ext_arguments("ext:convert", ext_convert_parser)
    '''
    # Options for selftest
    selftest_parser.add_argument("-l", "--list",
                               dest="install_list",
                               help="Test specified list of package(s)",
                               nargs="+")

    # Options for 'list'
    list_parser.add_argument("-v", "--verbose", action="store_true")

    # Options for 'config'
    file_option_group = config_parser.add_mutually_exclusive_group(required=True)
    file_option_group.add_argument("-u", "--update",
                                   help="Add any missing sections required for installed components",
                                   action="store_true")
    file_option_group.add_argument("-c", "--create",
                                   help="Create new config file with all required sections",
                                   action="store_true")
    config_parser.add_argument("filename",
                               help="Config file to write to; e.g. 'app.config'",
                               default="",
                               nargs="?")
    config_parser.add_argument("-l", "--list",
                                  dest="install_list",
                                  help="Config specified list of package(s)",
                                  nargs="+")

    # Options for 'run'
    run_parser.add_argument("-r", "--auto-restart",
                            help="Automatically restart all components if config file changes",
                            action="store_true")
    run_parser.add_argument("--config-file",
                            help="Pull configuration from specified file",
                            default=None)
    run_parser.add_argument("resilient_circuits_args", help="Args to pass to app.run", nargs=argparse.REMAINDER)

    # Options for 'service'
    service_parser.add_argument("--res-circuits-args",
                                help="Arguments to pass to resilient-circuits.exe run command",
                                action="store",
                                default="")
    service_parser.add_argument("service_args", help="Args to pass to service manager", nargs=argparse.REMAINDER)

    """
    # Options for codegen
    codegen_parser.add_argument("-p", "--package",
                                type=ensure_unicode,
                                help="Name of the package to generate")
    codegen_parser.add_argument("--reload",
                                metavar='PACKAGE',
                                type=ensure_unicode,
                                help="Reload customizations and create new customize.py")
    # Options for extract
    extractfile_parser.add_argument("--zip",
                                    action='store_true',
                                    help="zip of the resulting file")
    """
    # Options for 'customize'
    customize_parser.add_argument("-y",
                                  dest="yflag",
                                  help="Customize without prompting for confirmation",
                                  action="store_true")
    customize_parser.add_argument("-l", "--list",
                                  dest="install_list",
                                  help="Install specified list of package(s)",
                                  nargs="+")

    clone_parser.add_argument("--workflow",
                              help='Clone workflows. "old-api-name" "new-api-name". Workflows are based off of the'
                                   ' last export.',
                              nargs=2)

    args, unknown_args = parser.parse_known_args()
    if args.verbose:
        LOG.debug("Verbose Logging Enabled")
        LOG.setLevel(logging.DEBUG)

    if args.cmd != "run" and len(unknown_args) > 0:
        # Shouldn't have any unknown args for other commands, generate the proper errors
        args = parser.parse_args()

    if args.cmd == "run":
        run(unknown_args + args.resilient_circuits_args,
            restartable=args.auto_restart,
            config_file=args.config_file)
    elif args.cmd == "test":
        from resilient_circuits.bin import res_action_test
        res_action_test.ResilientTestProcessor().cmdloop()
    elif args.cmd == "config":
        generate_or_update_config(args)
    elif args.cmd == "list":
        list_installed(args)
    elif args.cmd == "service":
        manage_service(unknown_args + args.service_args, args.res_circuits_args)
    elif args.cmd in ("codegen", "extract"):
        LOG.warning("DEPRECATED: The '%s' command has been deprecated for resilient-circuits. "
                    "This functionality has been moved to the resilient-sdk tool.", args.cmd)
        """
        if args.cmd == "codegen" and args.package is None and args.function is None and args.reload is None:
            codegen_parser.print_usage()
        elif args.cmd == "extract" and args.output is None:
            extractfile_parser.print_usage()
        else:
            logging.basicConfig(format='%(message)s', level=logging.INFO)
            generate_code(args)
        """
    elif args.cmd == "customize":
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        customize_resilient(args)
    elif args.cmd == "clone":
        LOG.warning(DEPRECATION_MSG_CLONE)
        if args.workflow is None:
            print('Please specify a workflow to clone')
            clone_parser.print_usage()
        else:
            clone(args)
    elif args.cmd == "selftest":
        selftest(args)

    elif "ext:" in args.cmd:
        # Call the ext: command handler
        ext_command_handler(args.cmd, args)

if __name__ == "__main__":
    LOG.debug("CALLING MAIN")
    main()
