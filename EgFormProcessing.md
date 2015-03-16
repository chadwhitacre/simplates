# Example 4: Processing a Form #

This example introduces:

  1. `POST`ing to yourself
  1. accessing the `request` object from a simplate
  1. skipping the _template_ section

For this example, we will implement a simple contact form.


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

Note that we have enabled [the "request" context processor](http://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-request) (the others are [the defaults](http://docs.djangoproject.com/en/dev/ref/templates/api/#id1), which we don't want to lose). We need the `request` context processor in order to access the `request` object from our simplate, as we'll see below.


### urls.py ###

```
from django.conf.urls.defaults import *
from simplates.views import direct_to_simplate


urlpatterns = patterns('',
    (r'^contact.html$', direct_to_simplate),
)
```


### simplate at /path/to/simplates/contact.html ###

By now, you should know that a simplate has [up to three sections](EgRedirect.md), separated by this line:

```
#<!--===BREAK===-->
```

The sections are:

| 1. | **import** | Python, runs once |
|:---|:-----------|:------------------|
| 2. | **view** | Python, runs every request |
| 3. | **template** | Django template |

The objects from the Python sections are available in the template section.

Here is the content of our simplate for this example (compare this with [Django's contact form example without simplates](http://docs.djangoproject.com/en/1.0/topics/forms/#form-objects)):

```
import sys

from django import forms
from django.http import HttpResponseRedirect


class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)


#<!--===BREAK===-->

if request.method == 'POST':
    form = ContactForm(request.POST)
    if form.is_valid():
        # Process the data ...
        response = HttpResponseRedirect('/thanks.html')
        response.skip_template = True # Don't do template processing.
        sys.exit(response)
else:
    form = ContactForm()


#<!--===BREAK===-->

<form action="{{ request.META.PATH_INFO }}" method="POST">
{{ form.as_p }}
<input type="submit" value="Submit" />
</form>
```

Notice that we used `sys.exit(response)` here instead of `raise SystemExit(response)`. The two are equivalent in Python. Also notice that we added a special attribute to our `response` object: `skip_template`. This tells the simplate engine not to apply the templating section when we're going to be redirecting anyway.

## Next Example: [Generating an Image Dynamically](EgImageGeneration.md) ##