#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
Common Helper Functions specific to customize.py, config.py and setup.py files for the resilient-sdk
"""

import os
import logging
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.helpers import (load_py_module,
                                        read_file,
                                        rename_to_bak_file,
                                        write_file,
                                        rename_file)


# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


def load_customize_py_module(path_customize_py):
    """
    Return the path_customize_file as a Python Module.
    We can then access it methods like:
        > result = customize_py_module.codegen_reload_data()

    Raises an SDKException if we fail to load the module
    
    :param path_customize_py: Path to the customize.py file that contains the module
    :return: The customize Python Module, if found
    :rtype: module
    """
    LINE_TO_REPLACE = u"from resilient_circuits"
    REPLACE_TEXT = u"from resilient import ImportDefinition\n"

    # Try to load the customize.py module.
    # Some customize.py files (older) have a dependency on resilient_circuits.
    # In this case, the import will fail.
    # So if it does, we try replace the line of code in customize.py
    # that starts with "from resilient_circuits" with "from resilient import ImportDefinition".
    try:
        customize_py_module = load_py_module(path_customize_py, "customize")
    except ImportError as err:
        LOG.warning("WARNING: Failed to load customize.py\n%s", err.message)

        new_lines, path_backup_customize_py = [], ""
        current_customize_py_lines = read_file(path_customize_py)

        # Loop lines
        for i, line in enumerate(current_customize_py_lines):
            if line.startswith(LINE_TO_REPLACE):
                new_lines = current_customize_py_lines[:i] + [REPLACE_TEXT] + current_customize_py_lines[i + 1:]
                break

        # if new_lines means we have replaced some old lines
        if new_lines:

            # Create backup!
            path_backup_customize_py = rename_to_bak_file(path_customize_py)

            try:
                # Write the new customize.py
                write_file(path_customize_py, u"".join(new_lines))

                # Try loading again customize module
                customize_py_module = load_py_module(path_customize_py, "customize")

            except Exception as err:
                # If an error trying to load the module again and customize.py does not exist
                # rename the backup file to original
                if not os.path.isfile(path_customize_py):
                    LOG.info(u"An error occurred. Renaming customize.py.bak to customize.py")
                    rename_file(path_backup_customize_py, "customize.py")

                raise SDKException(u"Failed to load customize.py module\n{0}".format(err.message))

        # Else we did not match resilient_circuits, file corrupt.
        # We only support one instance of "from resilient_circuits"
        # If different means developer modified customize.py manually
        else:
            raise SDKException(u"Failed to load customize.py module. The file is corrupt\n{0}".format(err.message))

    return customize_py_module
