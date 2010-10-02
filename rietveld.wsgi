import os, sys
sys.path.append('/home/roundup/trackers/tracker/rietveld')
os.environ['DJANGO_SETTINGS_MODULE']='settings'
import django.core.handlers.wsgi
import gae2django
gae2django.install(server_software='Django')
application = django.core.handlers.wsgi.WSGIHandler()

