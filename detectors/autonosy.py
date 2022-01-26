# This auditor automatically adds users and release managers to the nosy
# list when the component fields gets set and the priority is changed to
# 'release blocker' respectively.
# See also the nosyreaction.py script (they should probably be merged to a
# single script).

RELEASE_MANAGERS = {
    'Python 3.7': '5248',  # ned.deily
    'Python 3.8': '12704', # lukasz.langa
    'Python 3.9': '12704', # lukasz.langa
    'Python 3.10': '26865', # pablogsal
    'Python 3.11': '26865', # pablogsal
}


def autonosy(db, cl, nodeid, newvalues):
    components = newvalues.get('components', [])

    current_nosy = set()
    if 'nosy' in newvalues:
        # the nosy list changed
        # newvalues['nosy'] contains all the user ids (new and old)
        nosy = newvalues.get('nosy', [])
        nosy = [value for value in nosy if db.hasnode('user', value)]
        current_nosy |= set(nosy)
    else:
        if nodeid:
            # the issue already exists
            # get the values that were already in the nosy
            old_nosy = db.issue.get(nodeid, 'nosy')
            current_nosy |= set(old_nosy)

    # make a copy of the current_nosy where to add the new user ids
    new_nosy = set(current_nosy)

    for component in components:
        users = db.component.get(component, 'add_as_nosy')
        new_nosy |= set(users)

    # get the new values if they changed or the already-set ones if they didn't
    if 'priority' in newvalues:
        priority_id = newvalues['priority']
    elif nodeid is not None:
        priority_id = db.issue.get(nodeid, 'priority')
    else:
        priority_id = None
    priority = 'None'
    if priority_id is not None:
        priority = db.priority.get(priority_id, 'name')

    versions = []
    if 'versions' in newvalues:
        versions = newvalues.get('versions', [])
    elif nodeid is not None:
        versions = db.issue.get(nodeid, 'versions')

    if priority == 'release blocker':
        for version in versions:
            name = db.version.get(version, 'name')
            if name in RELEASE_MANAGERS:
                new_nosy.add(RELEASE_MANAGERS[name])

    if current_nosy != new_nosy:
        # some user ids have been added automatically, so update the nosy
        newvalues['nosy'] = list(new_nosy)


def init(db):
    db.issue.audit('create', autonosy)
    db.issue.audit('set', autonosy)
