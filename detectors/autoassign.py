# Auditor to automatically assign issues to a user when
# the component field gets set

def autoassign(db, cl, nodeid, newvalues):
    try:
        components = newvalues['components']
    except KeyError:
        # Without components, nothing needs to be auto-assigned
        return
    if newvalues.has_key('assignee'):
        # If there is an explicit assignee in the new values
        # (even if it is None, in the case unassignment):
        # do nothing
        return
    # If the issue is already assigned, do nothing
    if nodeid and db.issue.get(nodeid, 'assignee'):
        return
    for component in components:
        user = db.component.get(component, 'assign_to')
        if user:
            # If there would be multiple auto-assigned users
            # arbitrarily pick the first one we find
            newvalues['assignee'] = user
            return

def init(db):
    db.issue.audit('create', autoassign)
    db.issue.audit('set', autoassign)
