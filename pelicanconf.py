#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'hyphenOs Software Labs. Pvt. Ltd.'
SITENAME = u'hyphenOs {-Os} Blog'
SITEURL = ''
SITELOGO = u'/images/hyphenos-white.svg'

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
LINKS = (
        ('hyphenOs Home', 'https://hyphenos.io/'),
        )

# Social widget
SOCIAL = (
        ('github', 'https://github.com/hyphenOs'),
          )

DEFAULT_PAGINATION = 10

THEME = 'theme/Flex'

PYGMENTS_STYLE = 'monokai'

STATIC_PATHS = ['images']


MARKDOWN = {'extension_configs':
                { 'markdown.extensions.extra': {},
                }
           }
# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
