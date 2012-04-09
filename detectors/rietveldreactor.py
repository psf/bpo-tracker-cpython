import cPickle, base64

# ListProperty is initialized to the cPickle of an empty list
empty_list = base64.encodestring(cPickle.dumps([]))

def create_django_user(db, cl, nodeid, oldvalues):
    username = cl.get(nodeid, 'username')
    email = cl.get(nodeid, 'address')
    if email is None:
        email = ''
    c = db.cursor
    # django.contrib.auth.models.UNUSABLE_PASSWORD=='!'
    c.execute("insert into auth_user(id, username, email, password, first_name, last_name, "
              "is_staff, is_active, is_superuser, last_login, date_joined) "
              "values(%s, %s, %s, '!', '', '', false, true, false, now(), now())",
              (nodeid, username, email))

def update_django_user(db, cl, nodeid, oldvalues):
    user = nodeid
    oldname = oldvalues['username']
    newname = cl.get(nodeid, 'username')
    if oldname != newname:
        c = db.cursor
        c.execute("update auth_user set username=%s where id=%s", (newname, user))

    old = oldvalues['address'].decode('ascii')
    new = cl.get(nodeid, 'address').decode('ascii')
    if old != new:
        c = db.cursor
        c.execute('update auth_user set email=%s where id=%s', (new, user))
        c.execute('update codereview_account set email=%s where id=%s', (new, user))
        # find issues where user is on nosy
        c.execute('select nodeid,cc from issue_nosy, codereview_issue '
                  'where linkid=%s and nodeid=id', (user,))
        for issue, cc in c.fetchall():
            cc = cPickle.loads(base64.decodestring(cc))
            try:
                cc[cc.index(old)] = new
            except ValueError:
                cc.append(new)
            cc = base64.encodestring(cPickle.dumps(cc))
            c.execute('update codereview_issue set cc=%s where id=%s', (cc, issue))
        

def update_issue_cc(db, cl, nodeid, oldvalues):
    if 'nosy' not in oldvalues:
        return
    c = db.cursor
    c.execute("select count(*) from codereview_issue where id=%s", (nodeid,))
    if c.fetchone()[0] == 0:
        return
    cc = []
    for user in db.issue.get(nodeid, 'nosy'):
        cc.append(db.user.get(user, 'address'))
    cc = base64.encodestring(cPickle.dumps(cc))
    c.execute("update codereview_issue set cc=%s where id=%s", (cc, nodeid))

def init(db):
    db.user.react('create', create_django_user)
    db.user.react('set', update_django_user)
    db.issue.react('set', update_issue_cc)
    # XXX react to email changes, roles
    # XXX react to subject, closed changes on issues
