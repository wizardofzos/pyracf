# Configuration file for the Sphinx documentation builder.
#
# https://samnicholls.net/2016/06/15/how-to-sphinx-readthedocs/
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pyRACF'
copyright = '2022-2024 Henri Kuiper; 2024 Rob van Hoboken'
author = 'Rob van Hoboken'
release = '0.9.0'
version = release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

#extensions = []
#extensions = ['sphinx.ext.napoleon']
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinx.ext.napoleon', 'sphinx_markdown_builder']

templates_path = ['_templates']
exclude_patterns = ['build/*', '_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]

# -- Options for markdown output -------------------------------------------------

# remove .md to ensure links work on github's Wiki
# markdown_http_base = ""
# markdown_uri_doc_suffix = ""


# -- autodoc configuration options ----------------------------------------------
autodoc_member_order = 'bysource'
import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../src'))
