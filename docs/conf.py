# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = 'Aveloxis'
copyright = '2026, Sean Goggins, University of Missouri, Derek Howard'
author = 'Sean P. Goggins'
release = '0.10.7'

extensions = [
    'myst_parser',
    'sphinx_rtd_theme',
]
myst_enable_extensions = ["html_image"]

# Support both .rst and .md files
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# MyST-Parser settings for Markdown support
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'fieldlist',
    'tasklist',
]
myst_heading_anchors = 3
