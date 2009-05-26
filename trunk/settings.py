import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))


ROOT_URLCONF = 'urls'

SIMPLATE_DIRS = (
    os.path.join(os.environ['BOX'], 'simplates'),
)

SIMPLATE_DEFAULTS = ('index.html', 'index.htm')

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request'
)

