# Example 5: Generating an Image Dynamically #

In this example we show two things:

  1. using the querystring
  1. serving dynamic content without a template

Let's assume that the [Python Imaging Library (PIL)](http://www.pythonware.com/products/pil/) is already installed. We are going to build off of [this example of integrating PIL with Django](http://effbot.org/zone/django-pil.htm) to serve rectangles of different colors via URLs of this form:

```
http://www.example.com/rectangle.png?ink={red,blue,green,yellow}
```


### settings.py ###

```
SIMPLATE_DIRS = (
    '/path/to/simplates',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request'
)
```

As [before](EgFormProcessing.md), we need to install the `request` context processor in `settings.py` in order to use API from Django's `request` object inside our simplate. In this case, we want to use `request.GET`.


### urls.py ###

```
from django.conf.urls.defaults import *
from simplates.views import direct_to_simplate


urlpatterns = patterns('',
    (r'^rectangle.png$', direct_to_simplate),
)
```


### simplate at /path/to/simplates/rectangle.png ###

This simplate will not have a template section. Instead, we are going to explicitly define a `response` object to hold the image data, and we will `raise` that via `SystemExit`. Note, however, that in order for the simplate engine to know how to interpret each section, we still need two section breaks. We simply leave the _template_ section empty, and the simplate engine knows not to try to apply it (that is, we don't need to use `response.skip_template` when the _template_ section is empty).

```
from django import http
from PIL import Image


INK = "red", "blue", "green", "yellow"


#<!--===BREAK===-->

ink = request.GET.get('ink', '').strip()

if ink not in INK:
    response = http.HttpResponseBadRequest()
else:
    response = http.HttpResponse()
    image = Image.new("RGB", (800, 600), ink)
    image.save(response, "PNG")

raise SystemExit(response)


#<!--===BREAK===-->
```


By now you've seen most of what simplates has to offer. Try it out and give us feedback!

## Next: [Installation](http://code.google.com/p/simplates/) ##