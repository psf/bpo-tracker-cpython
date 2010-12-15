# Auditor to automatically add users as nosy to issues when
# the component field gets set

# Python 2.3 ... 2.6 compatibility:
from roundup.anypy.sets_ import set

RELEASE_MANAGERS = {
    'Python 2.6': '19',   # barry
    'Python 2.7': '4455', # benjamin.peterson
    'Python 3.1': '4455', # benjamin.peterson
    'Python 3.2': '93',   # georg.brandl
}

def autonosy(db, cl, nodeid, newvalues):
    components = newvalues.get('components', [])

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

    # get the new values if they changed or the already-set ones if they didn't
    if 'priority' in newvalues:
        priority = db.priority.get(newvalues['priority'], 'name')
    else:
        priority = db.priority.get(db.issue.get(nodeid, 'priority'), 'name')
    if 'versions' in newvalues:
        versions = newvalues.get('versions', [])
    else:
        versions = db.issue.get(nodeid, 'versions')

    if priority == 'release blocker':
        for version in versions:
            name = db.version.get(version, 'name')
            if name in RELEASE_MANAGERS:
                nosy.add(RELEASE_MANAGERS[name])

    newvalues['nosy'] = list(nosy)


def init(db):
    db.issue.audit('create', autonosy)
    db.issue.audit('set', autonosy)

