def init_priority(db, cl, nodeid, newvalues):
    """ Make sure the priority is set on new issues"""

    if newvalues.has_key('priority') and newvalues['priority']:
        return

    normal = db.priority.lookup('normal')
    newvalues['priority'] = normal

def init(db):
    db.issue.audit('create', init_priority)
