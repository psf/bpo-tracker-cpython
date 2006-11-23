from roundup.password import Password

#
# TRACKER INITIAL PRIORITY AND STATUS VALUES
#

bug_type = db.getclass('bug_type')
bug_type.create(name='crash', order='1')
bug_type.create(name='compile error', order='2')
bug_type.create(name='resource usage', order='3')
bug_type.create(name='security', order='4')
bug_type.create(name='behavior', order='5')
bug_type.create(name='rfe', order='6')

component = db.getclass('component')
component.create(name='core', order='1')
component.create(name='distutils', order='2')
component.create(name='stdlib', order='3')

platform = db.getclass('platform')
platform.create(name='GNU/Linux', order='1')
platform.create(name='Solaris', order='2')
platform.create(name='WinXP', order='3')

version = db.getclass('version')
version.create(name='2.5', order='1')
version.create(name='3k', order='2')

severity = db.getclass('severity')
severity.create(name='critical', order='1')
severity.create(name='urgent', order='2')
severity.create(name='major', order='2')
severity.create(name='normal', order='2')
severity.create(name='minor', order='2')

status = db.getclass('status')
status.create(name='new', order='1')
status.create(name='open', order='2')
status.create(name='pending', description='user feedback required', order='3')
status.create(name='closed', order='4')

resolution = db.getclass('resolution')
resolution.create(name='fixed', order='1')
resolution.create(name='invalid', order='2')
resolution.create(name='duplicate', order='3')

#
# create the two default users
user = db.getclass('user')
user.create(username="admin", password=adminpw, address=admin_email, roles='Admin')
user.create(username="anonymous", roles='Anonymous')
user.create(username="user", password=Password("user"), roles="User")
user.create(username="devel", password=Password("devel"), roles="Developer")
user.create(username="coord", password=Password("coord"), roles="Coordinator")
