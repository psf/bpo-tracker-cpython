import sets
from roundup import roundupdb, hyperdb

def updatenosy(db, cl, nodeid, newvalues):
    '''Update the nosy list for changes to the assignee
    '''
    # nodeid will be None if this is a new node
    current_nosy = sets.Set()
    if nodeid is None:
        ok = ('new', 'yes')
    else:
        ok = ('yes',)
        # old node, get the current values from the node if they haven't
        # changed
        if not newvalues.has_key('nosy'):
            nosy = cl.get(nodeid, 'nosy')
            for value in nosy:
                current_nosy.add(value)

    # if the nosy list changed in this transaction, init from the new
    # value
    if newvalues.has_key('nosy'):
        nosy = newvalues.get('nosy', [])
        for value in nosy:
            if not db.hasnode('user', value):
                continue
            current_nosy.add(value)

    new_nosy = sets.Set(current_nosy)

    # add assignee(s) to the nosy list
    if newvalues.has_key('assignee') and newvalues['assignee'] is not None:
        propdef = cl.getprops()
        if isinstance(propdef['assignee'], hyperdb.Link):
            assignee_ids = [newvalues['assignee']]
        elif isinstance(propdef['assignee'], hyperdb.Multilink):
            assignee_ids = newvalues['assignee']
        for assignee_id in assignee_ids:
            new_nosy.add(assignee_id)

    # see if there's any new messages - if so, possibly add the author and
    # recipient to the nosy
    if newvalues.has_key('messages'):
        if nodeid is None:
            ok = ('new', 'yes')
            messages = newvalues['messages']
        else:
            ok = ('yes',)
            # figure which of the messages now on the issue weren't
            oldmessages = cl.get(nodeid, 'messages')
            messages = []
            for msgid in newvalues['messages']:
                if msgid not in oldmessages:
                    messages.append(msgid)

        # configs for nosy modifications
        add_author = getattr(db.config, 'ADD_AUTHOR_TO_NOSY', 'new')
        add_recips = getattr(db.config, 'ADD_RECIPIENTS_TO_NOSY', 'new')

        # now for each new message:
        msg = db.msg
        for msgid in messages:
            if add_author in ok:
                authid = msg.get(msgid, 'author')
                new_nosy.add(authid)

            # add on the recipients of the message
            if add_recips in ok:
                for recipient in msg.get(msgid, 'recipients'):
                    new_nosy.add(recipient)

    if current_nosy != new_nosy:
        # that's it, save off the new nosy list
        newvalues['nosy'] = list(new_nosy)

def addcreator(db, cl, nodeid, newvalues):
    assert None == nodeid, "addcreator called for existing node"
    nosy = newvalues.get('nosy', [])
    if not db.getuid() in nosy:
        nosy.append(db.getuid())
        newvalues['nosy'] = nosy
                         

def init(db):
    db.issue.audit('create', updatenosy)
    db.issue.audit('set', updatenosy)

    # Make sure creator of issue is added. Do this after 'updatenosy'. 
    db.issue.audit('create', addcreator, priority=110)
