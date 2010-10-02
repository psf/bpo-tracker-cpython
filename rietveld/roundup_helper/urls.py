from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('',
        ('review/', include('rietveld_helper.urls')),
    )
