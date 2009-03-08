from roundup.password import Password

#
# TRACKER INITIAL PRIORITY AND STATUS VALUES
#
stage = db.getclass('stage')
stage.create(name='test needed', order='2',
             description='A test which exercises the issue and can be used as'
                         ' a unit test is needed')
stage.create(name='needs patch', order='3',
             description='A patch is needed to fix the issue')
stage.create(name='patch review', order='4',
             description='A patch is available and is awaiting a review by a'
                         ' trusted developer')
stage.create(name='commit review', order='5',
             description='A patch is available and is awaiting a review by a'
                         ' core developer')
stage.create(name='committed/rejected', order='6',
             description='The issue has been resolved')

issue_type = db.getclass('issue_type')
issue_type.create(name='crash', order='1')
issue_type.create(name='compile error', order='2')
issue_type.create(name='resource usage', order='3')
issue_type.create(name='security', order='4')
issue_type.create(name='behavior', order='5')
issue_type.create(name='performance', order='6')
issue_type.create(name='feature request', order='7')

component = db.getclass('component')
component.create(name="None", order="1")
component.create(name="2to3 (2.x to 3.0 conversion tool)", order="2")
component.create(name="Build", order="3")
component.create(name="ctypes", order="4")
component.create(name="Demos and Tools", order="5")
component.create(name="Distutils", order="6")
component.create(name="Documentation", order="7")
component.create(name="Extension Modules", order="8")
component.create(name="IDLE", order="9")
component.create(name="Installation", order="10")
component.create(name="Interpreter Core", order="11")
component.create(name="Library (Lib)", order="12")
component.create(name="Macintosh", order="13")
component.create(name="Regular Expressions", order="14")
component.create(name="Tests", order="15")
component.create(name="Tkinter", order="16")
component.create(name="Unicode", order="17")
component.create(name="Windows", order="18")
component.create(name="XML", order="19")

version = db.getclass('version')
version.create(name='Python 3.1', order='1')
version.create(name='Python 3.0', order='2')
version.create(name='Python 2.7', order='3')
version.create(name='Python 2.6', order='4')
version.create(name='Python 2.5', order='5')
version.create(name='Python 2.4', order='6')
version.create(name='3rd party', order='7')


severity = db.getclass('severity')
severity.create(name='critical', order='1')
severity.create(name='urgent', order='2')
severity.create(name='major', order='3')
severity.create(name='normal', order='4')
severity.create(name='minor', order='5')

priority = db.getclass('priority')
priority.create(name='release blocker', order='1',
                description='Blocks a release')
priority.create(name='deferred blocker', order='2',
                description='Blocks a future release')
priority.create(name='critical', order='3',
                description='Might block a future release')
priority.create(name='high', order='4',
                description='Important but will not block')
priority.create(name='normal', order='5')
priority.create(name='low', order='6',
                description='E.g. spelling errors in documentation')

status = db.getclass('status')
status.create(name='open', order='1')
status.create(name='closed', order='2')
status.create(name='pending', order='3', description='user feedback required')

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

keyword = db.getclass("keyword")
keyword.create(name="26backport",
               description="Backport 3.0 feature from 2.6")
keyword.create(name="64bit",
               description="Affects 64-bit platforms only")
keyword.create(name="easy",
               description="This is an easy task (e.g. suitable for GHOP or "
                           "bug day beginners)")
keyword.create(name="needs review",
               description="This issue has a patch which needs the review of"
                           " a developer.")
keyword.create(name="patch",
               description="Contains patch")

#
# create the two default users
user = db.getclass('user')
user.create(username="admin", password=adminpw, address=admin_email, roles='Admin')
user.create(username="anonymous", roles='Anonymous')
