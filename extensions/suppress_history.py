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

def init(instance):
    instance.registerUtil('is_history_ok', is_history_ok)
