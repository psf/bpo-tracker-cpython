
import xmlrpclib
import socket
import time
import math
import re

from roundup.exceptions import Reject

REVPAT = re.compile(r'(r[0-9]+\b|rev(ision)? [0-9]+\b)')

def extract_classinfo(db, klass, nodeid, newvalues):
    if None == nodeid:
        node = newvalues
        content = newvalues['content']
    else:
        node = db.getnode(klass.classname, nodeid)
        content = klass.get(nodeid, 'content')

    if node.has_key('creation') or node.has_key('date'):
        nodets = node.get('creation', node.get('date')).timestamp()
    else:
        nodets = time.time()

    if node.has_key('author') or node.has_key('creator'):
        authorid = node.get('author', node.get('creator'))
    else:
        authorid = db.getuid()

    authorage = nodets - db.getnode('user', authorid)['creation'].timestamp()

    tokens = ["klass:%s" % klass.classname,
              "author:%s" % authorid,
              "authorage:%d" % int(math.log(authorage)),
              "hasrev:%s" % (REVPAT.search(content) is not None)]


    return (content, tokens)

def check_spambayes(db, content, tokens):
    try:
        spambayes_uri = db.config.detectors['SPAMBAYES_URI']
    except KeyError, e:
        return (False, str(e))

    try:
        server = xmlrpclib.ServerProxy(spambayes_uri, verbose=False)
    except IOError, e:
        return (False, str(e))


    try:
        prob = server.score({'content':content}, tokens, {})
        return (True, prob)
    except (socket.error, xmlrpclib.Error), e:
        return (False, str(e))


def check_spam(db, klass, nodeid, newvalues):
    """Auditor to score a website submission."""


    if newvalues.has_key('spambayes_score'):
        if not db.security.hasPermission('SB: May Classify', db.getuid()):
            raise ValueError, "You don't have permission to spamclassify messages"
        # Don't do anything if we're explicitly setting the score
        return

    if not newvalues.has_key('content'):
        # No need to invoke spambayes if the content of the message
        # is unchanged.
        return

    (content, tokens) = extract_classinfo(db, klass, nodeid, newvalues)
    (success, other) = check_spambayes(db, content, tokens)
    if success:
        newvalues['spambayes_score'] = other
        newvalues['spambayes_misclassified'] = False
    else:
        newvalues['spambayes_score'] = -1
        newvalues['spambayes_misclassified'] = True

def init(database):
    """Initialize auditor."""
    database.msg.audit('create', check_spam)
    database.msg.audit('set', check_spam)
    database.file.audit('create', check_spam)
    database.file.audit('set', check_spam)
