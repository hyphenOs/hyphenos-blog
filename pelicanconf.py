#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Abhijit Gadgil'
SITENAME = u'hyphenOs {-Os} Blog'
SITEURL = ''
SITELOGO = u'/images/hyphenos.svg'

PATH = 'content'

TIMEZONE = 'Asia/Kolkata'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('hyphenOs{-Os}', 'https://hyphenos.io/'),)

# Social widget
SOCIAL = (
        ('github', 'https://github.com/hyphenOs'),
          )

DEFAULT_PAGINATION = 10

#THEME = 'themes/pelican-bootstrap3'
#JINJA_ENVIRONMENT = {'extensions': ['jinja2.ext.i18n']}
#PLUGIN_PATHS = ['pelican-plugins', ]
#PLUGINS = ['i18n_subsites', ]

#THEME = 'hyphenOs-theme'
THEME = 'theme/Flex'

PYGMENTS_STYLE = 'monokai'

STATIC_PATHS = ['images']

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
