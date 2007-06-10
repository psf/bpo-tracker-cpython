"""
spamcheck.py - Auditor that consults a SpamBayes server and scores all form
submissions.  Submissions which are deemed to be spam are rejected.  For the
time being only reject submissions which are assumed to be spam (score >=
SPAM_CUTOFF).  Once a reasonable body of ham and spam submissions have been
built up you can consider whether to also reject unsure submissions (score >
HAM_CUTOFF).  The current settings make it less likely that you'll reject
valid submissions at the expense of manual checks to correct spammy items
which snuck by the screen.
"""

# These must match the xmlrpc_{host,port,path} settings in the SpamBayes
# server config.
HOST = "localhost"
PORT = "8001"
PATH = "/sbrpc"

# These must match the {ham,spam}_cutoff setting in the SpamBayes server
# config.
HAM_CUTOFF = 0.2
SPAM_CUTOFF = 0.85

import xmlrpclib

from roundup.exceptions import Reject

def check_spam(db, cl, nodeid, newvalues):
    uri = "http://%s:%s%s" % (HOST, PORT, PATH)
    server = xmlrpclb.ServerProxy(uri, verbose=False)
    try:
        prob = server.score(newvalues, [], {})
    except (socket.error, xmlrpclib.Fault):
        pass
    else:
        if prob >= CUTOFF:
            raise Reject

def init(db):
    db.file.audit('create', check_spam)
    db.file.audit('set', check_spam)
