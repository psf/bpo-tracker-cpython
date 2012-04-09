#!/usr/bin/python
# Update rietveld tables when the email address changes
# this updates auth_user.email, codereview_account.email 
# and codereview_issue.cc, based on the nosy list s
# it does not update codereview_issue.reviewers, since it would be
# too expensive to search all issues, and since the reviewers list
# is something that has to be filled out separately in Rietveld.
# It also does not update codereview_message, since these have already
# been sent with the email addresses recorded in the database.
#
# This script is now part of rietveldreactor

import sys, os, base64, cPickle
sys.path.insert(1,'/home/roundup/roundup/lib/python2.5/site-packages')
import roundup.instance

verbose = sys.argv[1:] == ['-v']

homedir = os.path.join(os.path.dirname(__file__), "..")
tracker = roundup.instance.open(homedir)
db = tracker.open('admin')
c = db.cursor

c.execute('select a.id, b.email, a._address from _user a, auth_user b '
          'where a.id=b.id and a._address != b.email')
for user, old, new in c.fetchall():
    old = old.decode('ascii')
    new = new.decode('ascii')
    if verbose:
        print "Update user", user, 'from', old, 'to ', new
    c.execute('update auth_user set email=%s where id=%s', (new, user))
    c.execute('update codereview_account set email=%s where id=%s', (new, user))
    # find issues where user is on nosy
    c.execute('select nodeid,cc from issue_nosy, codereview_issue '
              'where linkid=%s and nodeid=id', (user,))
    for nodeid, cc in c.fetchall():
        cc = cPickle.loads(base64.decodestring(cc))
        if verbose:
            print " Update issue", nodeid, cc
        try:
            cc[cc.index(old)] = new
        except ValueError:
            cc.append(new)
        cc = base64.encodestring(cPickle.dumps(cc))
        c.execute('update codereview_issue set cc=%s where id=%s', (cc, nodeid))
    
    db.conn.commit()


