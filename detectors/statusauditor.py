def init_status(db, cl, nodeid, newvalues):
    """ Make sure the status is set on new issues"""

    if newvalues.has_key('status') and newvalues['status']:
        return

    new_id = db.status.lookup('open')
    newvalues['status'] = new_id


def block_resolution(db, cl, nodeid, newvalues):
    """ If the issue has blockers, don't allow it to be resolved."""

    if nodeid is None:
        dependencies = []
    else:
        dependencies = cl.get(nodeid, 'dependencies')
    dependencies = newvalues.get('dependencies', dependencies)

    # don't do anything if there's no blockers or the status hasn't
    # changed
    if not dependencies or not newvalues.has_key('status'):
        return

    # format the info
    u = db.config.TRACKER_WEB
    s = ', '.join(['<a href="%sissue%s">%s</a>'%(u,id,id) for id in dependencies])
    if len(dependencies) == 1:
        s = 'issue %s is'%s
    else:
        s = 'issues %s are'%s

    # ok, see if we're trying to resolve
    if newvalues.get('status') and newvalues['status'] == db.status.lookup('closed'):
        raise ValueError, "This issue can't be closed until %s closed."%s


def resolve(db, cl, nodeid, newvalues):
    """Make sure status, resolution, and superseder values match."""

    status_change = newvalues.get('status')
    status_close = status_change and newvalues['status'] == db.status.lookup('closed')

    # Make sure resolution and superseder get only set when status->close
    if not status_change or not status_close:
        if newvalues.get('resolution') or newvalues.get('superseder'):
            raise ValueError, "resolution and superseder must only be set when a issue is closed"

    # Make sure resolution is set when status->close
    if status_close:
        if not newvalues.get('resolution'):
            raise ValueError, "resolution must be set when a issue is closed"

        # Make sure superseder is set when resolution->duplicate
        if newvalues['resolution'] == db.resolution.lookup('duplicate'):
            if not newvalues.get('superseder'):
                raise ValueError, "please provide a superseder when closing a issue as 'duplicate'"



def resolve_dependencies(db, cl, nodeid, oldvalues):
    """ When we resolve an issue that's a blocker, remove it from the
    blockers list of the issue(s) it blocks."""

    newstatus = cl.get(nodeid,'status')

    # no change?
    if oldvalues.get('status', None) == newstatus:
        return

    closed_id = db.status.lookup('closed')

    # interesting?
    if newstatus != closed_id:
        return

    # yes - find all the dependend issues, if any, and remove me from
    # their dependency list
    issues = cl.find(dependencies=nodeid)
    for issueid in issues:
        dependencies = cl.get(issueid, 'dependencies')
        if nodeid in dependencies:
            dependencies.remove(nodeid)
            cl.set(issueid, dependencies=dependencies)


def init(db):
    # fire before changes are made
    db.issue.audit('create', init_status)
    db.issue.audit('create', block_resolution)
    db.issue.audit('set', block_resolution)
    db.issue.audit('set', resolve)

    # adjust after changes are committed
    db.issue.react('set', resolve_dependencies)
