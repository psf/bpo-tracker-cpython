from roundup.password import Password

#
# TRACKER INITIAL PRIORITY AND STATUS VALUES
#

pri = db.getclass('priority')
pri.create(name='9', order='1')
pri.create(name='8', order='2')
pri.create(name='7', order='3')
pri.create(name='6', order='4')
pri.create(name='5', order='5')
pri.create(name='4', order='6')
pri.create(name='3', order='7')
pri.create(name='2', order='8')
pri.create(name='1', order='9')

stat = db.getclass('status')
stat.create(name='Open', order='1')
stat.create(name='Pending', order='2')
stat.create(name='Closed', order='3')
stat.create(name='Deleted', order='4')

group = db.getclass('group')
group.create(name='third_party', order='1')
group.create(name='AST', order='2')
group.create(name='feature_request', order='3')
group.create(name='irreproducible', order='4')
group.create(name='python3k', description='This bug relates to python 3000', order='5')



#
# create the two default users
user = db.getclass('user')
user.create(username="admin", password=adminpw,
    address=admin_email, roles='Admin')
user.create(username="anonymous", roles='Anonymous')

# add any additional database creation steps here - but only if you
# haven't initialised the database with the admin "initialise" command

user.create(username="user", password=Password("user"), roles="User")

# vim: set filetype=python sts=4 sw=4 et si
