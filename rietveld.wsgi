import os, sys
sys.path.append('/home/roundup/trackers/tracker/rietveld')
os.environ['DJANGO_SETTINGS_MODULE']='settings'
import django.core.handlers.wsgi
import gae2django
gae2django.install(server_software='Django')
_application = django.core.handlers.wsgi.WSGIHandler()
def application(environ, start_response):
    # Django's {%url%} template won't prefix script_name,
    # so clear it here and put everything in path_info
    environ['PATH_INFO'] = environ['SCRIPT_NAME']+environ['PATH_INFO']
    environ['SCRIPT_NAME'] = ''

    #start_response('200 Ok', [('Content-type', 'text/plain')])
    #return ["\n".join([':'.join((str(k),str(v))) for k,v in environ.items()])]

    return _application(environ, start_response)

