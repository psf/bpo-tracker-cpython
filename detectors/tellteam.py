from roundup import roundupdb

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
    for msgid in cl.get(nodeid, 'messages'):
        try:
            # note: last arg must be a list
            cl.send_message(nodeid, msgid, change_note, triage_email)
        except roundupdb.MessageSendError, message:
            raise roundupdb.DetectorError, message

def init(db):
    db.issue.react('create', newissuetriage)

# vim: set filetype=python ts=4 sw=4 et si
