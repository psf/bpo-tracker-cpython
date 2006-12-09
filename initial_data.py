from roundup.password import Password

#
# TRACKER INITIAL PRIORITY AND STATUS VALUES
#

issue_type = db.getclass('issue_type')
issue_type.create(name='crash', order='1')
issue_type.create(name='compile error', order='2')
issue_type.create(name='resource usage', order='3')
issue_type.create(name='security', order='4')
issue_type.create(name='behavior', order='5')
issue_type.create(name='rfe', order='6')

component = db.getclass('component')
component.create(name='core', order='1')
component.create(name='distutils', order='2')
component.create(name='stdlib', order='3')

version = db.getclass('version')
version.create(name='2.5', order='1')
version.create(name='3k', order='2')

severity = db.getclass('severity')
severity.create(name='critical', order='1')
severity.create(name='urgent', order='2')
severity.create(name='major', order='3')
severity.create(name='normal', order='4')
severity.create(name='minor', order='5')

priority = db.getclass('priority')
priority.create(name='immediate', order='1')
priority.create(name='urgent', order='2')
priority.create(name='high', order='3')
priority.create(name='normal', order='4')
priority.create(name='low', order='5')

status = db.getclass('status')
status.create(name='open', order='1')
status.create(name='closed', order='2')
status.create(name='pending', description='user feedback required', order='3')

resolution = db.getclass('resolution')
resolution.create(name='accepted', order='1')
resolution.create(name='duplicate', order='2')
resolution.create(name='fixed', order='3')
resolution.create(name='invalid', order='4')
resolution.create(name='later', order='5')
resolution.create(name='out of date', order='6')
resolution.create(name='postponed', order='7')
resolution.create(name='rejected', order='8')
resolution.create(name='remind', order='9')
resolution.create(name='wont fix', order='10')
resolution.create(name='works for me', order='11')

#
# create the two default users
user = db.getclass('user')
user.create(username="admin", password=adminpw, address=admin_email, roles='Admin')
user.create(username="anonymous", roles='Anonymous')
user.create(username="user", password=Password("user"), roles="User")
user.create(username="devel", password=Password("devel"), roles="Developer")
user.create(username="coord", password=Password("coord"), roles="Coordinator")
