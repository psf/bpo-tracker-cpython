# Reactor for sending changes to CIA.vc

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


def sendcia(db, cl, nodeid, newvalues):
    messages = set(newvalues.get('messages',()))
    messages -= set(cl.get(nodeid, 'messages'))
    if not messages:
        return
    messages = list(messages)

    log = '[#%d] ' % nodeid
    for msg in messages:
        log += db.msg.get(msg, 'content')
    if len(log) > max_content:
        log = log[:-4] + ' ...'

    params = parameters.copy()
    params['nodeid'] = nodeid
    params['author'] = db.user.get(db.getuid(), 'username')
    params['log'] = log

    payload = TEMPLATE % params

    open("/tmp/xxx", "w").write(payload)

def init(db):
    db.issue.audit('create', sendcia)
    db.issue.audit('set', sendcia)

