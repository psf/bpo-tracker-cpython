from roundup import roundupdb

def is_spam(db, msgid):
    cutoff_score = float(db.config.detectors['SPAMBAYES_SPAM_CUTOFF'])    

    msg = db.getnode("msg", msgid)
    if msg.has_key('spambayes_score') and \
           msg['spambayes_score'] > cutoff_score:
        return False
    return True

def newissuetriage(db, cl, nodeid, oldvalues):
    ''' Copy a message about new issues to a triage address, 
        set in detectors/config.ini
    '''
    # so use all the messages in the create
    change_note = cl.generateCreateNote(nodeid)

    # send a copy to the nosy list
    try:
        triage_email = db.config.detectors['TRIAGE_EMAIL'].split(",")
    except KeyError:
        triage_email = []
    if not triage_email:
        return
    for msgid in filter(lambda x: is_spam(db, x), cl.get(nodeid, 'messages')):
        try:
            # note: last arg must be a list
            
            cl.send_message(nodeid, msgid, change_note, triage_email)
        except roundupdb.MessageSendError, message:
            raise roundupdb.DetectorError, message

def init(db):
    db.issue.react('create', newissuetriage)

# vim: set filetype=python ts=4 sw=4 et si
