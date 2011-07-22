def is_history_ok(request):
    user = request.client.userid
    db = request.client.db
    classname = request.classname
    nodeid = request.nodeid
    # restrict display of user history to user itself only
    if classname == 'user':
        return user == nodeid or 'Coordinator' in db.user.get(user, 'roles')
    # currently not used
    return True

def is_coordinator(request):
    user = request.client.userid
    db = request.client.db
    return 'Coordinator' in db.user.get(user, 'roles')


def issueid_and_action_from_class(cls):
    """
    Return the id of the issue where the msg/file is/was linked
    and if the last "linking action" was 'link' or 'unlink'.
    """
    last_action = ''
    for entry in cls._klass.history(cls._nodeid):
        if 'unlink' in entry:
            last_unlink = entry
            last_action = 'unlink'
        elif 'link' in entry:
            last_entry = entry
            last_action = 'link'
    if last_action in ('link', 'unlink'):
        # the msg has been unlinked and not linked back
        # the link looks like: ('16', <Date 2011-07-22.05:14:12.342>, '4',
        #                       'link', ('issue', '1', 'messages'))
        return last_entry[4][1], last_action
    return None, None

def init(instance):
    instance.registerUtil('is_history_ok', is_history_ok)
    instance.registerUtil('is_coordinator', is_coordinator)
    instance.registerUtil('issueid_and_action_from_class',
                          issueid_and_action_from_class)
