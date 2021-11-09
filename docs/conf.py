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
import resilient_lib
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath("../resilient"))
sys.path.insert(0, os.path.abspath("../resilient_lib"))
sys.path.insert(0, os.path.abspath("../resilient_circuits"))


# -- Project information -----------------------------------------------------

project = 'IBM SOAR Python Libraries'
copyright = '2021, IBM'
author = 'IBM SOAR'
version = resilient_lib.__version__
release = resilient_lib.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx'
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
html_favicon = '_static/IBM_Security_Shield.ico?'
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
