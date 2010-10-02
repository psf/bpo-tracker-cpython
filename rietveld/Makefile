RIETVELDREV=510

default:
	@echo "Run 'make all' to fetch required sources to run this example."

all: static templates_svn codereview django gae2django syncdb
	@echo "Run './manage.py runserver 127.0.0.1:8000' to run Rietveld."

clean: clean_local clean_external

clean_external: clean_rietveld clean_django

clean_rietveld:
	rm -rf codereview static templates_svn

clean_django:
	unlink django

clean_local:
	unlink gae2django

gae2django:
	ln -s ../gae2django/gae2django .

syncdb:
	./manage.py syncdb

codereview:
	svn co http://rietveld.googlecode.com/svn/trunk/codereview@$(RIETVELDREV)
	patch -p0 < codereview.diff

static:
	svn co http://rietveld.googlecode.com/svn/trunk/static@$(RIETVELDREV)
	patch -p0 < patches/upload.diff

templates_svn:
	svn co http://rietveld.googlecode.com/svn/trunk/templates@$(RIETVELDREV) templates_svn

django:
	ln -s ../gae2django/django .
