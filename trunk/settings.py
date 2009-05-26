import os
import sys


DEBUG = True
ROOT = os.path.dirname(__file__)
ROOT_URLCONF = 'urls'
SIMPLATE_DIRS = (os.path.join(ROOT, 'tutorial'),)
SIMPLATE_DEFAULTS = ('index.html', 'index.htm')
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request'
)


sys.path.append(os.path.join(ROOT, 'apps'))
