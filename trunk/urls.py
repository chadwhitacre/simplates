from django.conf.urls.defaults import *
from simplates.views import direct_to_simplate


urlpatterns = patterns('',

    # Example 2
    ( r'^greetings/(?P<program>[^/]+)/$'
    , direct_to_simplate
    , {'simplate':'greetings/program.html'}
     ),

       
    # Example 3 
    (r'^old.html$', direct_to_simplate),
    (r'^new.html$', direct_to_simplate),

    
    # Example 4 
    (r'^contact.html$', direct_to_simplate),
    (r'^thanks.html$', direct_to_simplate),


    # Example 5 
    (r'^heading.png$', direct_to_simplate),


    # Example 1 (keep this last, eh?)
    (r'^$', direct_to_simplate),

)
