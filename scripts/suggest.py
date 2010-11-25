#!/usr/bin/python
# WSGI server to implement search suggestions
import ConfigParser, psycopg2, os, urllib, json

# copied from indexer_common
STOPWORDS = set([
    "A", "AND", "ARE", "AS", "AT", "BE", "BUT", "BY",
    "FOR", "IF", "IN", "INTO", "IS", "IT",
    "NO", "NOT", "OF", "ON", "OR", "SUCH",
    "THAT", "THE", "THEIR", "THEN", "THERE", "THESE",
    "THEY", "THIS", "TO", "WAS", "WILL", "WITH"
])

cfg = ConfigParser.ConfigParser({'password':'', 'port':''})
cfg.read(os.path.dirname(__file__)+"/../config.ini")
pgname = cfg.get('rdbms', 'name')
pguser = cfg.get('rdbms', 'user')
pgpwd = cfg.get('rdbms', 'password')
pghost = cfg.get('rdbms', 'host')
pgport = cfg.get('rdbms', 'port')

optparams = {}
if pghost: optparams['host'] = pghost
if pgport: optparams['port'] = pgport

conn = psycopg2.connect(database=pgname,
                        user=pguser,
                        password=pgpwd,
                        **optparams)
c = conn.cursor()

def escape_sql_like(s):
    return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

def suggest(query):
    words = query.upper().split()
    fullwords = [w for w in words[:-1]
                 if w not in STOPWORDS]
    partialword = words[-1]
    if fullwords:
        sql = 'select distinct(_textid) from __words where _word=%s'
        intersect = '\nINTERSECT\n'.join([sql]*len(fullwords))
        constraint = ' and _textid in ('+intersect+')'
    else:
        constraint = ''
    sql = ('select _word from __words where _word like %s '+constraint+
           'group by _word order by count(*) desc limit 10')
    c.execute(sql, (escape_sql_like(partialword)+'_%',)+tuple(fullwords))
    words = [w[0].lower() for w in c.fetchall()]
    conn.rollback()
    return json.dumps([query, words])    

def application(environ, start_response):
    # don't care about the URL here - just consider
    # the q query parameter
    query = urllib.unquote(environ['QUERY_STRING'])
    if not query:
        start_response('404 Not Found',[('Content-Type', 'text/html')])
        return ['<html><head><title>Not found</title></head>',
                '<body>The q query parameter is missing</body></html>']
    result = suggest(query)
    start_response('200 OK', 
                   [('Content-type', 'application/x-suggestions+json'),
                    ('Content-length', str(len(result)))])
    return [result]

if __name__=='__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8086, application)
    print "Serving on port 8086..."
    httpd.serve_forever()
