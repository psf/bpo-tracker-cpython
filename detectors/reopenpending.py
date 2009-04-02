def reopen_pending(db, cl, nodeid, newvalues):
    """Re-open pending issues when the issue is updated."""

    if newvalues.has_key('status'): return

    if nodeid is None: oldStatus = None
    else: oldStatus = cl.get(nodeid, 'status')
    if oldStatus == db.status.lookup('pending'):
        newvalues['status'] = db.status.lookup('open')


def init(db):
    # fire before changes are made
    db.issue.audit('set', reopen_pending)
