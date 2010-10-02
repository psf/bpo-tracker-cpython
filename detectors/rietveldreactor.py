import cPickle, base64

# ListProperty is initialized to the cPickle of an empty list
empty_list = base64.encodestring(cPickle.dumps([]))

def create_django_user(db, cl, nodeid, oldvalues):
    username = cl.get(nodeid, 'username')
    email = cl.get(nodeid, 'address')
    c = db.cursor
    # django.contrib.auth.models.UNUSABLE_PASSWORD=='!'
    c.execute("insert into auth_user(id, username, email, password, first_name, last_name, "
              "is_staff, is_active, is_superuser, last_login, date_joined) "
              "values(%s, %s, %s, '!', '', '', false, true, false, now(), now())",
              (nodeid, username, email))

def create_rietveld_issue(db, cl, nodeid, oldvalues):
    subject = cl.get(nodeid, 'title')
    c = db.cursor
    # find owner id: same in django as in rietveld
    owner_id = cl.get(nodeid, 'creator')
    c.execute("insert into codereview_issue(id, subject, owner_id, reviewers, cc, created, modified, closed, private, n_comments) "
              "values(%s, %s, %s, %s, %s, now(), now(), false, false, 0)",
              (nodeid, subject, owner_id, empty_list, empty_list))

def init(db):
    db.user.react('create', create_django_user)
    # XXX react to email changes, roles
    db.issue.react('create', create_rietveld_issue)
    # XXX reacto to subject, closed changes
