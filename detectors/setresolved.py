"""
A detector that sets the 'stage' field to 'resolved' when an issue is closed.
"""


def setresolved(db, cl, nodeid, newvalues):
    status_change = newvalues.get('status')
    status_close = status_change and status_change == db.status.lookup('closed')

    if status_close:
        if newvalues.get('stage') is None:
            newvalues['stage'] = db.stage.lookup('resolved')


def init(db):
    db.issue.audit('set', setresolved)
