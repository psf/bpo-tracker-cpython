#
# TRACKER SCHEMA
#

# Class automatically gets these properties:
#   creation = Date()
#   activity = Date()
#   creator = Link('user')
#   actor = Link('user')

# Issue Type
issue_type = Class(db, 'issue_type',
                   name=String(),
                   description=String(),
                   order=Number())
issue_type.setkey('name')

# Component
component = Class(db, 'component',
                  name=String(),
                  description=String(),
                  order=Number(),
                  assign_to=Link('user'),
                  add_as_nosy=Multilink('user'))
component.setkey('name')

# Version
version = Class(db, 'version',
                name=String(),
                description=String(),
                order=Number())
version.setkey('name')

# Severity
severity = Class(db, 'severity',
                 name=String(),
                 description=String(),
                 order=Number())
severity.setkey('name')

# Priority
priority = Class(db, 'priority',
                 name=String(),
                 description=String(),
                 order=Number())
priority.setkey('name')

# Stage
stage = Class(db, 'stage',
              name = String(),
              description = String(),
              order = Number())
stage.setkey('name')

# Status
status = Class(db, "status",
               name=String(),
               description=String(),
               order=Number())
status.setkey("name")

# Resolution
resolution = Class(db, "resolution",
                   name=String(),
                   description=String(),
                   order=Number())
resolution.setkey('name')

# Keyword
keyword = Class(db, "keyword",
                name=String(),
                description=String())
keyword.setkey("name")

# User-defined saved searches
query = Class(db, "query",
              klass=String(),
              name=String(),
              url=String(),
              private_for=Link('user'))

# add any additional database schema configuration here

user = Class(db, "user",
             username=String(),
             password=Password(),
             address=String(),
             realname=String(),
             phone=String(),
             organisation=String(),
             alternate_addresses=String(),
             queries=Multilink('query'),
             roles=String(),     # comma-separated string of Role names
             timezone=String(),
             contrib_form=Boolean(),
             contrib_form_date=Date(),
             openids=String(), # space separated list
             iscommitter=Boolean(),
             )
user.setkey("username")
db.security.addPermission(name='Register', klass='user',
                          description='User is allowed to register new user')

openid_session = Class(db, 'openid_session',
                       provider_id=String(), # or user id
                       url=String(),
                       stypes=String(), # space-separated list of session types
                       assoc_handle=String(),
                       expires=Date(),
                       mac_key=String())
openid_session.setkey('assoc_handle')
openid_session.disableJournalling()

openid_nonce = Class(db, 'openid_nonce',
                     created=Date(),
                     nonce=String())
openid_nonce.setkey('nonce')

# FileClass automatically gets this property in addition to the Class ones:
#   content = String()    [saved to disk in <tracker home>/db/files/]
#   type = String()       [MIME type of the content, default 'text/plain']
msg = FileClass(db, "msg",
                author=Link("user", do_journal='no'),
                recipients=Multilink("user", do_journal='no'),
                date=Date(),
                summary=String(),
                files=Multilink("file"),
                messageid=String(),
                inreplyto=String(),
                spambayes_score=Number(),
                spambayes_misclassified=Boolean(),)

file = FileClass(db, "file",
                 name=String(),
                 description=String(indexme='yes'),
                 spambayes_score=Number(),
                 spambayes_misclassified=Boolean(),
                 # filled out if this is a patch
                 revision=String(),
                 branch=String(),
                 # filled out if a corresponding Rietveld
                 # patchset exists for the issue
                 patchset=String(),)

hgrepo = Class(db, "hgrepo",
               url=String(),
               lastrev=String(),
               patchbranch=String(),
               )

# IssueClass automatically gets these properties in addition to the Class ones:
#   title = String()
#   messages = Multilink("msg")
#   files = Multilink("file")
#   nosy = Multilink("user")
#   superseder = Multilink("issue")
issue = IssueClass(db, "issue",
                   type=Link('issue_type'),
                   components=Multilink('component'),
                   versions=Multilink('version'),
                   severity=Link('severity'),
                   priority=Link('priority'),
                   dependencies=Multilink('issue'),
                   assignee=Link('user'),
                   status=Link('status'),
                   resolution=Link('resolution'),
                   superseder=Link('issue'),
                   keywords=Multilink("keyword"),
                   stage=Link('stage'),
                   nosy_count=Number(),
                   message_count=Number(),
                   hgrepos=Multilink('hgrepo'))

#
# TRACKER SECURITY SETTINGS
#
# See the configuration and customisation document for information
# about security setup.

db.security.addRole(name='Developer', description='A developer')
db.security.addRole(name='Coordinator', description='A coordinator')

db.security.addPermission(name="SB: May Classify")
db.security.addPermission(name="SB: May Report Misclassified")

#
# REGULAR USERS
#
# Give the regular users access to the web and email interface
for r in 'User', 'Developer', 'Coordinator':
    db.security.addPermissionToRole(r, 'Web Access')
    db.security.addPermissionToRole(r, 'Email Access')

##########################
# User permissions
##########################

for cl in ('issue_type', 'severity', 'component',
           'version', 'priority', 'stage', 'status', 'resolution',
           'issue', 'keyword', 'hgrepo'):
    db.security.addPermissionToRole('User', 'View', cl)
    db.security.addPermissionToRole('Anonymous', 'View', cl)

def may_edit_hgrepo(db, userid, itemid):
    return userid == db.hgrepo.get(itemid, "creator")
db.security.addPermissionToRole('User', 'Create', 'hgrepo')
p = db.security.addPermission(name='Edit', klass='hgrepo', check=may_edit_hgrepo,
                              properties=['url', 'patchbranch'])
db.security.addPermissionToRole('User', p)

class may_view_spam:
    def __init__(self, klassname):
        self.klassname = klassname

    def __call__(self, db, userid, itemid):
        cutoff_score = float(db.config.detectors['SPAMBAYES_SPAM_CUTOFF'])
        klass = db.getclass(self.klassname)

        try:
            score = klass.get(itemid, 'spambayes_score')
        except (KeyError, IndexError):
            return True

        if score > cutoff_score:
            return False

        return True

for cl in ('file', 'msg'):
    p = db.security.addPermission(name='View', klass=cl,
                                  description="allowed to see metadata object regardless of spam status",
                                  properties=('creation', 'activity',
                                              'creator', 'actor',
                                              'name', 'spambayes_score',
                                              'spambayes_misclassified',
                                              'author', 'recipients',
                                              'date', 'files', 'messageid',
                                              'inreplyto', 'type',
                                              'description',
                                              ))

    db.security.addPermissionToRole('Anonymous', p)
    db.security.addPermissionToRole('User', p)

    db.security.addPermissionToRole('User', 'Create', cl)

    p = db.security.addPermission(name='View', klass=cl,
                                  description="Allowed to see content of object regardless of spam status",
                                  properties = ('content', 'summary'))
    
    db.security.addPermissionToRole('User', p)        
    
    spamcheck = db.security.addPermission(name='View', klass=cl,
                                          description="allowed to see content if not spam",
                                          properties=('content', 'summary'),
                                          check=may_view_spam(cl))

    db.security.addPermissionToRole('Anonymous', spamcheck)

def may_edit_file(db, userid, itemid):
    return userid == db.file.get(itemid, "creator")
p = db.security.addPermission(name='Edit', klass='file', check=may_edit_file,
    description="User is allowed to remove their own files")
db.security.addPermissionToRole('User', p)

p = db.security.addPermission(name='Create', klass='issue',
                              properties=('title', 'type',
                                          'components', 'versions',
                                          'severity',
                                          'messages', 'files', 'nosy'),
                              description='User can report and discuss issues')
db.security.addPermissionToRole('User', p)

p = db.security.addPermission(name='Edit', klass='issue',
                              properties=('title', 'type',
                                          'components', 'versions',
                                          'severity',
                                          'messages', 'files', 'nosy', 'hgrepos'),
                              description='User can report and discuss issues')
db.security.addPermissionToRole('User', p)

# Allow users to close issues they created
def close_own_issue(db, userid, itemid):
    return userid == db.issue.get(itemid, 'creator')
p = db.security.addPermission(name='Edit', klass='issue',
                              properties=('status', 'resolution'),
                              description='User can close issues he created',
                              check=close_own_issue)
db.security.addPermissionToRole('User', p)

db.security.addPermissionToRole('User', 'SB: May Report Misclassified')



##########################
# Developer permissions
##########################
for cl in ('issue_type', 'severity', 'component',
           'version', 'priority', 'stage', 'status', 'resolution',
           'issue', 'file', 'msg', 'keyword'):
    db.security.addPermissionToRole('Developer', 'View', cl)

for cl in ('issue', 'file', 'msg', 'keyword'):
    db.security.addPermissionToRole('Developer', 'Edit', cl)
    db.security.addPermissionToRole('Developer', 'Create', cl)


##########################
# Coordinator permissions
##########################
for cl in ('issue_type', 'severity', 'component',
           'version', 'priority', 'stage', 'status', 'resolution', 'issue', 
           'file', 'msg', 'hgrepo'):
    db.security.addPermissionToRole('Coordinator', 'View', cl)
    db.security.addPermissionToRole('Coordinator', 'Edit', cl)
    db.security.addPermissionToRole('Coordinator', 'Create', cl)
    p = db.security.addPermission(name='Retire', klass=cl,
                                  description='Coordinator may retire '+cl)
    db.security.addPermissionToRole('Coordinator', p)

db.security.addPermissionToRole('Coordinator', 'SB: May Classify')

# May users view other user information? Comment these lines out
# if you don't want them to
db.security.addPermissionToRole('User', 'View', 'user')
db.security.addPermissionToRole('Developer', 'View', 'user')
db.security.addPermissionToRole('Coordinator', 'View', 'user')

# Allow Coordinator to edit any user, including their roles.
db.security.addPermissionToRole('Coordinator', 'Edit', 'user')
db.security.addPermissionToRole('Coordinator', 'Web Roles')

# Users should be able to edit their own details -- this permission is
# limited to only the situation where the Viewed or Edited item is their own.
def own_record(db, userid, itemid):
    '''Determine whether the userid matches the item being accessed.'''
    return userid == itemid
p = db.security.addPermission(name='View', klass='user', check=own_record,
    description="User is allowed to view their own user details")
for r in 'User', 'Developer', 'Coordinator':
    db.security.addPermissionToRole(r, p)
p = db.security.addPermission(name='Edit', klass='user', check=own_record,
    description="User is allowed to edit their own user details",
    properties=('username', 'password',
                'address', 'realname',
                'phone', 'organisation',
                'alternate_addresses',
                'queries',
                'timezone')) # Note: 'roles' excluded - users should not be able to edit their own roles.
                             # Also excluded: contrib_form, contrib_form_date, iscommitter
for r in 'User', 'Developer':
    db.security.addPermissionToRole(r, p)

# Users should be able to edit and view their own queries. They should also
# be able to view any marked as not private. They should not be able to
# edit others' queries, even if they're not private
def view_query(db, userid, itemid):
    private_for = db.query.get(itemid, 'private_for')
    if not private_for: return True
    return userid == private_for
def edit_query(db, userid, itemid):
    return userid == db.query.get(itemid, 'creator')
p = db.security.addPermission(name='View', klass='query', check=view_query,
    description="User is allowed to view their own and public queries")
for r in 'User', 'Developer', 'Coordinator':
    db.security.addPermissionToRole(r, p)
p = db.security.addPermission(name='Edit', klass='query', check=edit_query,
    description="User is allowed to edit their queries")
for r in 'User', 'Developer', 'Coordinator':
    db.security.addPermissionToRole(r, p)
p = db.security.addPermission(name='Create', klass='query',
    description="User is allowed to create queries")
for r in 'User', 'Developer', 'Coordinator':
    db.security.addPermissionToRole(r, p)


#
# ANONYMOUS USER PERMISSIONS
#
# Let anonymous users access the web interface. Note that almost all
# trackers will need this Permission. The only situation where it's not
# required is in a tracker that uses an HTTP Basic Authenticated front-end.
db.security.addPermissionToRole('Anonymous', 'Web Access')

# Let anonymous users access the email interface (note that this implies
# that they will be registered automatically, hence they will need the
# "Create" user Permission below)
# This is disabled by default to stop spam from auto-registering users on
# public trackers.
#db.security.addPermissionToRole('Anonymous', 'Email Access')

# Assign the appropriate permissions to the anonymous user's Anonymous
# Role. Choices here are:
# - Allow anonymous users to register
db.security.addPermissionToRole('Anonymous', 'Register', 'user')

# Allow anonymous users access to view issues (and the related, linked
# information).
# Note permissions settings for file and msg above (due to spambayes
# integration).

for cl in 'issue', 'severity', 'status', 'resolution':
    db.security.addPermissionToRole('Anonymous', 'View', cl)

# [OPTIONAL]
# Allow anonymous users access to create or edit "issue" items (and the
# related file and message items)
#for cl in 'issue', 'file', 'msg':
#   db.security.addPermissionToRole('Anonymous', 'Create', cl)
#   db.security.addPermissionToRole('Anonymous', 'Edit', cl)


# vim: set filetype=python sts=4 sw=4 et si :
