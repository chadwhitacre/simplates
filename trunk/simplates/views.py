import mimetypes
import os
from os.path import exists, isfile

import os
import stat
import threading
import traceback
import sys

import util
from django.conf import settings
from django.conf.urls.defaults import patterns
from django.core.handlers.wsgi import WSGIHandler
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.template import loader, loader_tags # gets us "extends," etc.


ENCODING = 'UTF-8'
MODE_STPROD = True 
MODE_DEBUG = False
BREAK = '#<!--===BREAK===-->'


class LoadError(StandardError):
    """Represent a problem parsing a simplate.
    """


# Cache helpers
# =============

class Entry:
    """An entry in the global simplate cache.
    """

    fspath = ''         # The filesystem path [string]
    modtime = None      # The timestamp of the last change [datetime.datetime]
    lock = None         # Access control for this record [threading.Lock]
    triple = None       # A post-processed version of the data [3-tuple]
    exc = None          # Any exception in reading or compilation [Exception]

    def __init__(self):
        """Populate with dummy data or an actual db entry.
        """
        self.fspath = ''
        self.modtime = 0
        self.lock = threading.Lock()
        self.triple = ()


class Locks:
    checkin = threading.Lock()
    checkout = threading.Lock()


__cache = dict()        # cache
__locks = Locks()       # access controls for __cache


# Core loader
# ===========

def load_simplate_uncached(fspath):
    """Given a filesystem path, return three objects (uncached).

    A simplate is a Django template with two optional Python components at the
    head of the file, delimited by '#<!--===BREAK===-->'. The first Python
    section is exec'd when the simplate is first called, and the namespace it
    populates is saved for all subsequent runs (so make sure it is
    thread-safe!). The second Python section is exec'd within the template
    namespace each time the template is rendered.

    """
    simplate = open(fspath).read().decode(ENCODING)

    nbreaks = simplate.count(BREAK)
    if nbreaks == 0:
        view = imports = ""
        template = simplate
    elif nbreaks == 1:
        imports = ""
        view, template = simplate.split(BREAK)
        view += BREAK
    elif nbreaks == 2:
        imports, view, template = simplate.split(BREAK)
        imports += '\n'
        view += '\n'
    else:
        raise SyntaxError( "Simplate <%s> may have at most two " % fspath
                         + "section breaks; it has %d." % nbreaks
                          )

    # Standardize newlines.
    # =====================
    # compile requires \n, and doing it now makes the next line easier.

    imports = imports.replace('\r\n', '\n')
    view = view.replace('\r\n', '\n')


    # Pad the beginning of the view section so we get accurate tracebacks.
    # ====================================================================

    view = ''.join(['\n' for n in range(imports.count('\n'))]) + view


    # Prep our cachable objects and return.
    # =====================================

    namespace = dict()
    namespace['__file__'] = fspath
    view = compile(view, fspath, 'exec')
    if template.strip():
        template = Template(template)
    else:
        template = None

    exec compile(imports, fspath, 'exec') in namespace

    return (namespace, view, template)


# Cache wrapper
# =============

def load_simplate_cached(fspath):
    """Given a filesystem path, return three objects (with caching).
    """

    # Check out an entry.
    # ===================
    # Each entry has its own lock, and "checking out" an entry means
    # acquiring that lock. If a simplate isn't yet in our cache, we first
    # "check in" a new dummy entry for it (and prevent other threads from
    # adding the same simplate), which will be populated presently.

    #thread_id = threading.currentThread().getName()[-1:] # for debugging
    #call_id = ''.join([random.choice(string.letters) for i in range(5)])

    __locks.checkout.acquire()
    try: # critical section
        if fspath in __cache:

            # Retrieve an already cached simplate.
            # ====================================
            # The cached entry may be a dummy. The best way to guarantee we
            # will catch this case is to simply refresh our entry after we
            # acquire its lock.

            entry = __cache[fspath]
            entry.lock.acquire()
            entry = __cache[fspath]

        else:

            # Add a new entry to our cache.
            # =============================

            dummy = Entry()
            dummy.fspath = fspath
            dummy.lock.acquire()
            __locks.checkin.acquire()
            try: # critical section
                if fspath in __cache:
                    # Someone beat us to it. @@: can this actually happen?
                    entry = __cache[fspath]
                else:
                    __cache[fspath] = dummy
                    entry = dummy
            finally:
                __locks.checkin.release()

    finally:
        __locks.checkout.release() # Now that we've checked out our simplate, 
                                   # other threads are free to check out other 
                                   # simplates.


    # Process the simplate.
    # =====================

    try: # critical section

        # Decide whether it's a hit or miss.
        # ==================================

        modtime = os.stat(fspath)[stat.ST_MTIME]
        if entry.modtime == modtime:                            # cache hit
            if entry.exc is not None:
                raise entry.exc
        else:                                                   # cache miss
            try:
                entry.triple = load_simplate_uncached(fspath)
                entry.exc = None
            except Exception, exception:
                # NB: Old-style string exceptions will still raise.
                entry.exc = ( LoadError(traceback.format_exc())
                            , sys.exc_info()[2]
                             )


        # Check the simplate back in.
        # ===========================

        __locks.checkin.acquire()
        try: # critical section
            entry.modtime = modtime
            __cache[fspath] = entry
            if entry.exc is not None:
                raise entry.exc[0]
        finally:
            __locks.checkin.release()

    finally:
        entry.lock.release()


    # Return
    # ======
    # Avoid mutating the cached namespace dictionary.

    namespace, view, template = entry.triple
    namespace = namespace.copy()
    return (namespace, view, template)


# Django wrapper
# ==============

def direct_to_simplate(request, *args, **params):
    """Django view to exec and render a simplate.
    """

    # 1. Translate to filesystem.
    # ===========================
    # Our algorithm for computing the fs path varies based on whether a 
    # specific simplate is named, or it is to be taken from PATH_INFO.

    if 'simplate' in params:
        simplate_path = os.path.join(*params['simplate'].split('/'))
        del params['simplate']
        def compute_fspath(root):
            return os.path.join(root, simplate_path)
    else:
        path_info = request.META['PATH_INFO']
        def compute_fspath(root):
            fspath = util.translate(root, path_info)
            fspath = util.find_default(settings.SIMPLATE_DEFAULTS, fspath)
            return fspath

    for root in settings.SIMPLATE_DIRS:
        fspath = compute_fspath(root)
        if os.path.isfile(fspath):
            break

    assert os.path.isfile(fspath), "No default simplate found in %s." % fspath
    #@: make this error message more helpful


    # 2. Load simplate.
    # =================

    namespace, view, template = load_simplate_cached(fspath)


    # 3. Populate namespace.
    # ======================
    # Exec operates on a dictionary, but Django templates don't take a straight 
    # dict, they take a RequestContext (which is basically several overlapping 
    # dictionaries). So we have to go back and forth.

    for i in range(len(args)):
        params[i] = arg[i]
    namespace['params'] = params
    template_context = RequestContext(request, namespace)


    # 4. Exec the view.
    # =================

    response = None
    if view:
        for d in template_context.dicts:
            namespace.update(d)
        try:
            exec view in namespace
        except SystemExit, exc:
            if len(exc.args) > 0:
                response = exc.args[0]
        template_context.update(namespace)


    # 5. Get a response object.
    # =========================

    if response is not None:                # explicit
        if not isinstance(response, HttpResponse):
            raise TypeError("Simplate exits with an invalid response.")
    else:
        response = HttpResponse()           # implicit


    # 5. Process the template.
    # ========================
    # If template is None that means that that section was empty.
    #
    # For this and the next step, we allow the user to override us by setting 
    # skip_{template,mimetype} on the response object. We then use getattr to 
    # access each attribute, because, in the default case, the attribute will
    # not exist (that is, it's not part of the Django class).

    if not getattr(response, 'skip_template', False): # response.skip_template
        if template is not None:
            response.write(template.render(template_context))


    # 6. Set the mimetype.
    # ====================
    # Note that we guess based on the filesystem path, not the URL path.
    
    if not getattr(response, 'skip_mimetype', False): # response.skip_mimetype
        guess = mimetypes.guess_type(fspath, 'text/plain')[0]
        if guess is None:
            guess = settings.DEFAULT_CONTENT_TYPE
            # FYI, the default through trunk/r6670 (includes 0.96) is text/html
        if guess.startswith('text/'):
            guess += "; charset=%s" % settings.DEFAULT_CHARSET
        response['Content-Type'] = guess


    # 7. Return.
    # ==========

    return response


# Simplate
# ========
# Wrapper for specifying a single simplate for multiple URLs in urls.py.

class Simplate(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, request, *args, **kwargs):
        kwargs['simplate'] = self.path
        return direct_to_simplate(request, *args, **kwargs)

