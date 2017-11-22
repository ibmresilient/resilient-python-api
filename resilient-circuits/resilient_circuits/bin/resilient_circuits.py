#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Command line tool to manage and run resilient-circuits """
from __future__ import absolute_import

import argparse
import logging
import os, os.path
import pkg_resources
import re
import sys
import traceback
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

from collections import defaultdict

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

def windows_service(service_args, res_circuits_args):
    try:
        import win32serviceutil
        from resilient_circuits.bin import service_wrapper

        if res_circuits_args:
            # Set the command line arguments to pass to "resilient-circuits.exe run"
            service_wrapper.irms_svc.setResilientArgs(res_circuits_args)

        sys.argv=sys.argv[0:1] + service_args
        win32serviceutil.HandleCommandLine(service_wrapper.irms_svc)
    except ImportError:
        LOG.error("Requires PYWIN32 Package. Please download and install from: "
                  "https://sourceforge.net/projects/pywin32/files/pywin32/")

def supervisor_service():
    pass

def manage_service(service_args, res_circuits_args):
    if os.name == 'nt':
        windows_service(service_args, res_circuits_args)
    else:
        supervisor_service(service_args, res_circuits_args)

def run(resilient_circuits_args, restartable=False, config_file=None):
    """Run resilient-circuits"""
    # Leave only the arguments for the run command
    if restartable:
        # import here b/c it is slow
        from resilient_circuits import app_restartable as app
    else:
        from resilient_circuits import app
    sys.argv=sys.argv[0:1] + resilient_circuits_args
    kwargs = {}
    if config_file:
        kwargs = {"config_file": config_file}
    app.run(**kwargs)

def list_installed():
    """print list of installed packages with their components"""
    LOG.debug("resilient-circuits.list")
    components = defaultdict(list)
    entry_points = [ep for ep in pkg_resources.iter_entry_points('resilient.circuits.components')]
    LOG.debug("Found %d installed components", len(entry_points))
    for ep in entry_points:
        components[ep.dist].append(ep.name)
    if not components:
        LOG.info("No resilient-circuits components are installed")
        return
    LOG.info("The following packages and components are installed:")
    for dist, component_list in components.items():
        pkg = dist.project_name
        version = dist._version
        LOG.info("%s (%s) installed components:\n\t%s",
                 pkg,
                 version,
                 "\n\t".join(component_list))

def discover_required_config_sections():
    """return list of functions to call to generate sample config sections"""
    entry_points = pkg_resources.iter_entry_points('resilient.circuits.configsection')
    return [ep.load() for ep in entry_points]

def generate_default():
    """ return string containing entire default app.config """
    base_config_fn = pkg_resources.resource_filename("resilient_circuits", "data/app.config.base")
    with open(base_config_fn, 'r') as base_config_file:
        base_config = base_config_file.read()
        additional_sections = [func() for func  in discover_required_config_sections()]
        LOG.debug("Found %d sections to generate", len(additional_sections))
        return "\n\n".join(([base_config,] + additional_sections))

def generate_or_update_config(args):
    """ Create or update config file based on installed components """
    usage_type = "CREATING" if args.create else "UPDATING"

    if not args.filename:
        # Use default config file in ~/.resilient/app.config and create directory if missing
        config_filename = os.path.expanduser(os.path.join("~", ".resilient", "app.config"))
        resilient_dir = os.path.dirname(config_filename)
        if not os.path.exists(resilient_dir):
            LOG.info("Creating %s", resilient_dir)
            os.makedirs(resilient_dir)
    else:
        config_filename = os.path.expandvars(os.path.expanduser(args.filename))
    file_exists = os.path.exists(config_filename)

    if file_exists:
        if args.create:
            choice = ""
            while choice not in ('y', 'n'):
                choice = input("%s exists. Do you want to overwrite? y/n: " % config_filename)
            if choice == 'n':
                LOG.error("Config file creation cancelled.")
                return
    elif args.update:
        LOG.error("File %s does not exist. Update cancelled.", config_filename)
        return

    LOG.info("%s config file %s", usage_type, config_filename)

    if args.create:
        # Write out default file
        with open(config_filename, "w+", encoding="utf-8") as config_file:
            config_file.write(generate_default())
            LOG.info("Config generated. %s  Please manually edit with your specific configuration values", config_filename)

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

        with open(config_filename, "a", encoding="utf-8") as config_file:
            for config_data in [func() for func  in discover_required_config_sections()]:
                required_config = configparser.ConfigParser(interpolation=None)
                LOG.debug("Config Data String:\n%s", config_data)
                required_config.read_string(unicode(config_data))
                new_section = required_config.sections()[0]
                LOG.debug("Required Section: %s", new_section)
                if new_section not in existing_sections:
                    # Add the default data for this required section to the config file
                    LOG.info("Adding new section %s", new_section)
                    config_file.write(u"\n" + config_data)
                    updated = True
                else:
                    LOG.debug("Section %s already present, not adding", new_section)

            if updated:
                LOG.info("Update finished. New sections may require manual edits with your specific configuration values")
            else:
                LOG.info("No updates required.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Print debug output", action="store_true")

    subparsers = parser.add_subparsers(title="subcommands",
                                       help="one of these options must be provided",
                                       description="valid subcommands",
                                       dest="cmd")
    subparsers.required = True
    list_parser = subparsers.add_parser("list",
                                        help="List the installed Resilient Circuits components")
    run_parser = subparsers.add_parser("run",
                                       help="Run the Resilient Circuits application")
    service_parser = subparsers.add_parser("service",
                                           help="Manage Resilient Circuits as a service with Windows or Supervisord")
    config_parser = subparsers.add_parser("config",
                                          help="Create or update a basic configuration file")

    file_option_group = config_parser.add_mutually_exclusive_group(required=True)
    file_option_group.add_argument("-u", "--update",
                                   help="Add any missing sections required for installed components",
                                   action="store_true")
    file_option_group.add_argument("-c", "--create",
                                   help="Create new config file with all required sections",
                                   action="store_true")
    config_parser.add_argument("filename",
                               help="Config file to write to; e.g. 'app.config'",
                               default= "",
                               nargs = "?")

    run_parser.add_argument("-r", "--auto-restart",
                            help="Automatically restart all components if config file changes",
                            action="store_true")
    run_parser.add_argument("--config-file",
                            help="Pull configuration from specified file",
                            default=None)
    run_parser.add_argument("resilient_circuits_args", help="Args to pass to app.run", nargs=argparse.REMAINDER)


    service_parser.add_argument("--res-circuits-args",
                                help="Arguments to pass to resilient-circuits.exe run command",
                                action="store",
                                default="")
    service_parser.add_argument("service_args", help="Args to pass to service manager", nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()
    if args.verbose:
        LOG.debug("Verbose Logging Enabled")
        LOG.setLevel(logging.DEBUG)

    if args.cmd != "run" and len(unknown_args) > 0:
        # Shouldn't have any unknown args for other commands, generate the proper errors
        args = parser.parse_args()

    if args.cmd == "config":
        generate_or_update_config(args)
    elif args.cmd == "run":
        run(unknown_args + args.resilient_circuits_args,
            restartable=args.auto_restart,
            config_file=args.config_file)
    elif args.cmd == "list":
        list_installed()
    elif args.cmd == "service":
        manage_service(unknown_args + args.service_args,
                       args.res_circuits_args)

if __name__ == "__main__":
    LOG.debug("CALLING MAIN")
    main()
