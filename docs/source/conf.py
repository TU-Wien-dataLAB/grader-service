# -- Project information -----------------------------------------------------

project = "Grader Service"
copyright = "2024"
author = "TU Wien dataLAB"
# language = "fr"  # For testing language translations

master_doc = "index"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "ablog",
    "myst_nb",
    "autodoc_traits",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "sphinx_examples",
    "sphinx_tabs.tabs",
    "sphinx_thebe",
    "sphinx_togglebutton",
    "sphinx.ext.todo",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

nitpick_ignore = [
    ("py:class", "docutils.nodes.document"),
    ("py:class", "docutils.parsers.rst.directives.body.Sidebar"),
]

suppress_warnings = ["myst.domains", "ref.ref"]

numfig = True

myst_enable_extensions = ["dollarmath", "amsmath", "deflist", "colon_fence"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"
html_logo = "_static/assets/images/logo_name.png"
html_title = "Sphinx Book Theme"
html_copy_source = True
html_favicon = "_static/assets/images/logo_name.png"
html_last_updated_fmt = ""

html_sidebars = {
    "reference/blog/*": [
        "navbar-logo.html",
        "search-field.html",
        "ablog/postcard.html",
        "ablog/recentposts.html",
        "ablog/tagcloud.html",
        "ablog/categories.html",
        "ablog/archives.html",
        "sbt-sidebar-nav.html",
    ]
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
nb_execution_mode = "cache"

html_theme_options = {
    "path_to_docs": "docs",
    "repository_url": "https://github.com/TU-Wien-dataLAB/Grader-Service",
    "repository_branch": "master",
    "launch_buttons": {
        "binderhub_url": "https://mybinder.org",
        "colab_url": "https://colab.research.google.com/",
        "deepnote_url": "https://deepnote.com/",
        "notebook_interface": "jupyterlab",
        "thebe": True,
    },
    "use_edit_page_button": True,
    "use_source_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "use_sidenotes": True,
    "show_toc_level": 3,
    "logo": {"image_dark": "_static/assets/images/logo_name.png"},
    "icon_links": [
        {
            "name": "GitHub Grader Service",
            "url": "https://github.com/TU-Wien-dataLAB/Grader-Service",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI Grader Service",
            "url": "https://pypi.org/project/grader-service/",
            "icon": "https://img.shields.io/pypi/v/grader-service",
            "type": "url",
        },
        {
            "name": "TU Wien dataLAB",
            "url": "https://www.it.tuwien.ac.at/en/services/network-and-servers/datalab",
            "icon": "_static/assets/images/tu-logo.svg",
            "type": "url",
        },
    ],
}

ogp_social_cards = {"image": "_static/assets/images/logo_name.png"}
