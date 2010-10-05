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

def init(db):
    db.user.react('create', create_django_user)
    # XXX react to email changes, roles
    # XXX react to subject, closed changes on issues
