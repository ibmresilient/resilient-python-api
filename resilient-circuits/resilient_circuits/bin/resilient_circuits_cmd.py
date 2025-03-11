#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Command line tool to manage and run resilient-circuits """
import argparse
import logging
import os
import sys
from collections import defaultdict
import pkg_resources
from resilient import get_config_file
from resilient_circuits import helpers, constants
from resilient_circuits.util.resilient_customize import customize_resilient
from resilient_circuits.cmds import selftest


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

LOG = logging.getLogger(constants.CMDS_LOGGER_NAME)
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

    LOG.info(helpers.get_env_str(pkg_resources.working_set))

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


def main():
    """Main commandline"""

    parser = argparse.ArgumentParser(
        prog="resilient-circuits",
        description="Runtime environment for apps used with IBM Security SOAR",
        epilog="For support, please visit https://ibm.biz/soarcommunity"
    )

    parser.usage = """
    $ resilient-circuits <subcommand> ...
    $ resilient-circuits -v <subcommand> ...
    $ resilient-circuits -h
    """

    parser.add_argument("-v", "--verbose", help="Set the log level to DEBUG", action="store_true")

    subparsers = parser.add_subparsers(title="subcommands",
                                       description="one of these options must be provided",
                                       metavar="",
                                       dest="cmd")

    subparsers.required = True

    run_parser = subparsers.add_parser("run",
                                       help="Run the Resilient Circuits application")

    list_parser = subparsers.add_parser("list",
                                        help="List the installed Resilient Circuits components")

    test_parser = subparsers.add_parser("test",
                                        help="(Deprecated) Run an interactive client for testing Resilient Circuits messages")

    service_parser = subparsers.add_parser("service",
                                           help="Manage Resilient Circuits as a service")

    config_parser = subparsers.add_parser("config",
                                          help="Create or update a basic configuration file")

    customize_parser = subparsers.add_parser("customize",
                                             help="Apply customizations to the Resilient platform")

    selftest_parser = subparsers.add_parser("selftest",
                                            help="Call selftest functions for every package and print their return states")

    # Options for selftest
    selftest_parser.add_argument("-l", "--list",
                                 dest="install_list",
                                 help="Test specified list of package(s)",
                                 nargs="+")

    selftest_parser.add_argument("--print-env",
                                 help="Print Python version and list installed Packages",
                                 action="store_true")

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

    # Options for 'customize'
    customize_parser.add_argument("-y",
                                  dest="yflag",
                                  help="Customize without prompting for confirmation",
                                  action="store_true")

    customize_parser.add_argument("-l", "--list",
                                  dest="install_list",
                                  help="Install specified list of package(s)",
                                  nargs="+")

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

    elif args.cmd == "customize":
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        customize_resilient(args)

    elif args.cmd == "selftest":
        selftest.execute_command(args)


if __name__ == "__main__":
    LOG.debug("CALLING MAIN")
    main()
