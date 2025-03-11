# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from importlib import metadata

import resilient_lib
from resilient_sdk import app as sdk_app
from resilient_sdk.cmds import (CmdClone, CmdCodegen, CmdDocgen, CmdExtPackage,
                                CmdExtract, CmdRunInit, CmdList, CmdValidate)
from resilient_sdk.util.sdk_helpers import parse_optionals

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath("../resilient"))
sys.path.insert(0, os.path.abspath("../resilient_lib"))
sys.path.insert(0, os.path.abspath("../resilient_circuits"))
sys.path.insert(0, os.path.abspath("../resilient_sdk"))


# -- Project information -----------------------------------------------------

project = 'IBM SOAR Python Libraries'
copyright = '2023, IBM'
author = 'IBM SOAR'
version = resilient_lib.__version__
release = resilient_lib.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'

html_title = "IBM SOAR Python Documentation"
html_favicon = '_static/IBM_Security_Shield.ico'
html_theme_options = {
    "light_logo": "IBM_Security_Light.png",
    "dark_logo": "IBM_Security_Dark.png",
}
html_use_index = False
html_show_sourcelink = False
html_domain_indices = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# autodoc configs
add_module_names = False

# copybutton extension configs
copybutton_prompt_text = "$ "

# resilient-sdk parser
sdk_parser = sdk_app.get_main_app_parser()
sdk_sub_parser = sdk_app.get_main_app_sub_parser(sdk_parser)

cmd_codegen = CmdCodegen(sdk_sub_parser)
cmd_docgen = CmdDocgen(sdk_sub_parser)
cmd_ext_package = CmdExtPackage(sdk_sub_parser)
cmd_clone = CmdClone(sdk_sub_parser)
cmd_extract = CmdExtract(sdk_sub_parser)
cmd_validate = CmdValidate(sdk_sub_parser)
cmd_init = CmdRunInit(sdk_sub_parser)
cmd_list = CmdList(sdk_sub_parser)

# parse the setup.py files
the_globals = {
    "__file__": "",
    "long_description": "",
    "_python_requires": ""
}
resilient_setup_attributes = metadata.metadata("resilient")
circuits_setup_attributes = metadata.metadata("resilient-circuits")
lib_setup_attributes = metadata.metadata("resilient-lib")
sdk_setup_attributes = metadata.metadata("resilient-sdk")
jinja_filters = ", ".join(list(resilient_lib.components.templates_common.JINJA_FILTERS.keys()))

# make variables available in .rst files
rst_epilog = f"""
.. |resilient_desc| replace:: {resilient_setup_attributes.get("Summary")}
.. |circuits_desc| replace:: {circuits_setup_attributes.get("Summary")}
.. |lib_desc| replace:: {lib_setup_attributes.get("Summary")}
.. |lib_jinja_filters| replace:: {jinja_filters}
.. |sdk_desc| replace:: {sdk_setup_attributes.get("Summary")}
.. |sdk_parser_desc| replace:: {sdk_parser.description}
.. |sdk_parser_usage| replace:: {sdk_parser.usage}
.. |sdk_options| replace:: {parse_optionals(sdk_parser._get_optional_actions())}
.. |cmd_codegen_desc| replace:: {cmd_codegen.parser.description}
.. |cmd_codegen_usage| replace:: {cmd_codegen.parser.usage}
.. |cmd_codegen_options| replace:: {parse_optionals(cmd_codegen.parser._get_optional_actions())}
.. |cmd_docgen_desc| replace:: {cmd_docgen.parser.description}
.. |cmd_docgen_usage| replace:: {cmd_docgen.parser.usage}
.. |cmd_docgen_options| replace:: {parse_optionals(cmd_docgen.parser._get_optional_actions())}
.. |cmd_package_desc| replace:: {cmd_ext_package.parser.description}
.. |cmd_package_usage| replace:: {cmd_ext_package.parser.usage}
.. |cmd_package_options| replace:: {parse_optionals(cmd_ext_package.parser._get_optional_actions())}
.. |cmd_clone_desc| replace:: {cmd_clone.parser.description}
.. |cmd_clone_usage| replace:: {cmd_clone.parser.usage}
.. |cmd_clone_options| replace:: {parse_optionals(cmd_clone.parser._get_optional_actions())}
.. |cmd_extract_desc| replace:: {cmd_extract.parser.description}
.. |cmd_extract_usage| replace:: {cmd_extract.parser.usage}
.. |cmd_extract_options| replace:: {parse_optionals(cmd_extract.parser._get_optional_actions())}
.. |cmd_validate_desc| replace:: {cmd_validate.parser.description}
.. |cmd_validate_usage| replace:: {cmd_validate.parser.usage}
.. |cmd_validate_options| replace:: {parse_optionals(cmd_validate.parser._get_optional_actions())}
.. |cmd_init_desc| replace:: {cmd_init.parser.description}
.. |cmd_init_usage| replace:: {cmd_init.parser.usage}
.. |cmd_init_options| replace:: {parse_optionals(cmd_init.parser._get_optional_actions())}
.. |cmd_list_desc| replace:: {cmd_list.parser.description}
.. |cmd_list_usage| replace:: {cmd_list.parser.usage}
.. |cmd_list_options| replace:: {parse_optionals(cmd_list.parser._get_optional_actions())}
"""
