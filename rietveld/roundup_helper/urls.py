from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('',
        ('python-dev/', 'roundup'),
        ('review/', include('rietveld_helper.urls')),
    )
