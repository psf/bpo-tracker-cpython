# Reactor for sending changes to CIA.vc
import xmlrpclib

server = "http://CIA.vc"

parameters = {
    'name':'Roundup Reactor for CIA',
    'revision': "$Revision$"[11:-2],
    'project': 'python',
    'module': 'Roundup',
    'urlprefix': 'http://bugs.python.org/issue',
}

max_content = 150

TEMPLATE = """
<message>
<generator>
  <name>Roundup Reactor for CIA</name>
  <version>%(revision)s</version>
</generator>
<source>
  <project>%(project)s</project>
  <module>%(module)s</module>
</source>
<body>
  <commit>
    <author>%(author)s</author>
    <log>%(log)s</log>
    <url>%(urlprefix)s%(nodeid)s</url>
  </commit>
</body>
</message>
"""


def sendcia(db, cl, nodeid, oldvalues):
    messages = set(cl.get(nodeid, 'messages'))
    if oldvalues:
        messages -= set(oldvalues.get('messages',()))
    if not messages:
        return
    messages = list(messages)

    log = '[#%s] ' % nodeid
    for msg in messages:
        log += db.msg.get(msg, 'content')
    if len(log) > max_content:
        log = log[:-4] + ' ...'

    params = parameters.copy()
    params['nodeid'] = nodeid
    params['author'] = db.user.get(db.getuid(), 'username')
    params['log'] = log

    payload = TEMPLATE % params

    try: 
        rpc = xmlrpclib.ServerProxy(server)
        rpc.hub.deliver(payload)
    except:
        # Ignore any errors in sending the CIA;
        # if the server is down, that's just bad luck
        # XXX might want to do some logging here
        pass

def init(db):
    db.issue.react('create', sendcia)
    db.issue.react('set', sendcia)

