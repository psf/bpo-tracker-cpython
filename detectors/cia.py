# Reactor for sending changes to CIA.vc
import xmlrpclib
import cgi

server = "http://CIA.vc"

parameters = {
    'name':'Roundup Reactor for CIA',
    'revision': "$Revision$"[11:-2],
    'project': 'Python',
    'branch': 'roundup',
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
  <module>#%(nodeid)s</module>
  <branch>%(branch)s</branch>
</source>
<body>
  <commit>
    <author>%(author)s</author>
    <files><file>%(file)s</file></files>
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

    if oldvalues:
        oldstatus = oldvalues['status']
    else:
        oldstatus = None
    newstatus = db.issue.get(nodeid, 'status')
    if oldstatus != newstatus:
        if oldvalues:
            status = db.status.get(newstatus, 'name')
        else:
            status = 'new'
        log = '[' + status + '] '
    else:
        log = ''
    for msg in messages:
        log += db.msg.get(msg, 'content')
    if len(log) > max_content:
        log = log[:max_content-4] + ' ...'
    log = log.replace('\n', ' ')

    params = parameters.copy()
    params['file'] = cgi.escape(db.issue.get(nodeid, 'title'))
    params['nodeid'] = nodeid
    params['author'] = db.user.get(db.getuid(), 'username')
    params['log'] = cgi.escape(log)

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
