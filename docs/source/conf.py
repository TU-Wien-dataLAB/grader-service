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
# import os
# import sys
# sys.path.insert(0, os.path.abspath('../../grader_service'))


# -- Project information -----------------------------------------------------

project = 'Grader Service'
copyright = '2023, Marijana Petojevic, Matthias Matt, Florian Jäger, Elias Wimmer'
author = 'Marijana Petojevic, Matthias Matt, Florian Jäger, Elias Wimmer'

# The full version, including alpha/beta/rc tags
from grader_service._version import __version__
release = __version__

# -- General configuration ---------------------------------------------------

add_module_names = False

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc",
              "sphinx.ext.autosummary",
              "sphinx.ext.doctest",
              "sphinx.ext.extlinks",
              "sphinx.ext.viewcode",
              "sphinx.ext.todo",
              "numpydoc",  # handle NumPy documentation formatted docstrings
              "sphinx.ext.intersphinx",
              "sphinx.ext.coverage",
              "sphinx.ext.mathjax",
              "sphinx.ext.ifconfig",]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

numpydoc_show_class_members = False


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'pydata_sphinx_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

html_sidebars = {
    "**": ["search-field.html", "sidebar-nav-bs.html", "sidebar-ethical-ads.html"]
}
