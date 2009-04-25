# Auditor to automatically add users as nosy to issues when
# the component field gets set

# Python 2.3 ... 2.6 compatibility:
from roundup.anypy.sets_ import set

def autonosy(db, cl, nodeid, newvalues):

    if 'components' not in newvalues:
        # Without components, nobody needs to be added as nosy
        return
    else:
        components = newvalues['components']

    nosy = set()
    if 'nosy' in newvalues:
        new_nosy = newvalues.get('nosy', [])
        new_nosy = [value for value in new_nosy if db.hasnode('user', value)]
        nosy |= set(new_nosy)
    else:
        if nodeid:
            old_nosy = db.issue.get(nodeid, 'nosy')
            nosy |= set(old_nosy)

    for component in components:
        users = db.component.get(component, 'add_as_nosy')
        nosy |= set(users)

    newvalues['nosy'] = list(nosy)


def init(db):
    db.issue.audit('create', autonosy)
    db.issue.audit('set', autonosy)

