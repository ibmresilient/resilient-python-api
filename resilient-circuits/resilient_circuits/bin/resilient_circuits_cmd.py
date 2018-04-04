#!/usr/bin/env python
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
from resilient_circuits.app import AppArgumentParser
from resilient_circuits.util.resilient_codegen import list_functions, codegen_functions, codegen_package
from resilient_circuits.util.resilient_customize import customize_resilient

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


LOG = logging.getLogger(__name__)
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
    LOG.info(u"The following packages and components are installed:")
    for dist, component_list in components.items():
        if args.verbose:
            clist = "\n\t".join([str(ep) for ep in component_list if ep in component_entry_points])
            if clist == "":
                LOG.info(u"%s (%s):\n\t(Package does not define any components)",
                         dist.as_requirement(),
                         dist.egg_info)
            else:
                LOG.info(u"%s (%s):\n\t%s",
                         dist.as_requirement(),
                         dist.egg_info,
                         clist)
        else:
            clist = "\n\t".join([ep.name for ep in component_list if ep in component_entry_points])
            if clist == "":
                LOG.info(u"%s:\n\t(Package does not define any components)",
                         dist.as_requirement())
            else:
                LOG.info(u"%s:\n\t%s",
                         dist.as_requirement(),
                         clist)


def generate_default():
    """ return string containing entire default app.config """
    base_config_fn = pkg_resources.resource_filename("resilient_circuits", "data/app.config.base")
    entry_points = pkg_resources.iter_entry_points('resilient.circuits.configsection')
    additional_sections = []
    for entry in entry_points:
        dist = entry.dist
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
    with open(base_config_fn, 'r') as base_config_file:
        base_config = base_config_file.read()
        return "\n\n".join(([base_config, ] + additional_sections))


def generate_or_update_config(args):
    """ Create or update config file based on installed components """
    usage_type = "CREATING" if args.create else "UPDATING"

    if not args.filename:
        # Use default config file in ~/.resilient/app.config and create directory if missing
        config_filename = os.path.expanduser(os.path.join("~", ".resilient", "app.config"))
        resilient_dir = os.path.dirname(config_filename)
        if not os.path.exists(resilient_dir):
            LOG.info(u"Creating %s", resilient_dir)
            os.makedirs(resilient_dir)
    else:
        config_filename = os.path.expandvars(os.path.expanduser(args.filename))
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
            config_file.write(generate_default())
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

        with open(config_filename, "a", encoding="utf-8") as config_file:
            for entry in entry_points:
                dist = entry.dist
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
                    # Add the default data for this required section to the config file
                    LOG.info(u"Adding new section '%s' for '%s'", new_section, dist)
                    config_file.write(u"\n" + config_data)
                    updated = True
                else:
                    LOG.debug(u"Section '%s' already present, not adding", new_section)

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

    if args.package:
        # codegen an installable package
        output_base = os.path.join(os.curdir, args.package)
        codegen_package(client, args.exportfile, args.package,
                        args.messagedestination, args.function, args.workflow, args.rule,
                        args.field, args.datatable, args.task, args.script,
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
        codegen_functions(client, args.exportfile, args.function, args.workflow, args.rule, output_dir, output_file)


def main():
    """Main commandline"""
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
    codegen_parser = subparsers.add_parser("codegen",
                                           help="Generate template code for Python components")
    customize_parser = subparsers.add_parser("customize",
                                             help="Apply customizations to the Resilient platform")

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

    # Options for 'codegen'
    codegen_parser.add_argument("-p", "--package",
                                help="Name of the package to generate")
    codegen_parser.add_argument("-o", "--output",
                                help="Output file name")
    codegen_parser.add_argument("-f", "--function",
                                help="Generate code for the specified function(s)",
                                nargs="*")
    codegen_parser.add_argument("-m", "--messagedestination",
                                help="Generate code for all functions that use the specified message destination(s)",
                                nargs="*")
    codegen_parser.add_argument("--workflow",
                                help="Include customization data for workflow(s)",
                                nargs="*")
    codegen_parser.add_argument("--rule",
                                help="Include customization data for rule(s)",
                                nargs="*")
    codegen_parser.add_argument("--field",
                                help="Include customization data for incident field(s)",
                                nargs="*")
    codegen_parser.add_argument("--datatable",
                                help="Include customization data for datatable(s)",
                                nargs="*")
    codegen_parser.add_argument("--task",
                                help="Include customization data for automatic task(s)",
                                nargs="*")
    codegen_parser.add_argument("--script",
                                help="Include customization data for script(s)",
                                nargs="*")
    codegen_parser.add_argument("--exportfile",
                                help="Generate based on organization export file (.res)")

    # Options for 'customize'
    customize_parser.add_argument("-y",
                                  dest="yflag",
                                  help="Customize without prompting for confirmation",
                                  action="store_true")

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
    elif args.cmd == "codegen":
        if args.package is None and args.function is None:
            codegen_parser.print_usage()
        else:
            logging.basicConfig(format='%(message)s', level=logging.INFO)
            generate_code(args)
    elif args.cmd == "customize":
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        customize_resilient(args)


if __name__ == "__main__":
    LOG.debug("CALLING MAIN")
    main()
