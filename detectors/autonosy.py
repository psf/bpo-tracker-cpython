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

    if 'priority' in newvalues:
        if db.priority.get(newvalues['priority'], 'name') == 'release blocker':
            for version in db.issue.get(nodeid, 'versions'):
                name = db.version.get(version, 'name')
                if name in RELEASE_MANAGERS:
                    nosy.add(RELEASE_MANAGERS[name])

    newvalues['nosy'] = list(nosy)


def init(db):
    db.issue.audit('create', autonosy)
    db.issue.audit('set', autonosy)

