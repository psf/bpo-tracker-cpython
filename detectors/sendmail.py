from roundup import roundupdb

def determineNewMessages(cl, nodeid, oldvalues):
    ''' Figure a list of the messages that are being added to the given
        node in this transaction.
    '''
    messages = []
    if oldvalues is None:
        # the action was a create, so use all the messages in the create
        messages = cl.get(nodeid, 'messages')
    elif oldvalues.has_key('messages'):
        # the action was a set (so adding new messages to an existing issue)
        m = {}
        for msgid in oldvalues['messages']:
            m[msgid] = 1
        messages = []
        # figure which of the messages now on the issue weren't there before
        for msgid in cl.get(nodeid, 'messages'):
            if not m.has_key(msgid):
                messages.append(msgid)
    return messages


def is_spam(db, msgid):
    """Return true if message has a spambayes score above
    db.config.detectors['SPAMBAYES_SPAM_CUTOFF']. Also return true if
    msgid is None, which happens when there are no messages (i.e., a
    property-only change)"""
    if not msgid:
        return False
    cutoff_score = float(db.config.detectors['SPAMBAYES_SPAM_CUTOFF'])    

    msg = db.getnode("msg", msgid)
    if msg.has_key('spambayes_score') and \
           msg['spambayes_score'] > cutoff_score:
        return True
    return False


def sendmail(db, cl, nodeid, oldvalues):
    """Send mail to various recipients, when changes occur:

    * For all changes (property-only, or with new message), send mail
      to all e-mail addresses defined in
      db.config.detectors['BUSYBODY_EMAIL']

    * For all changes (property-only, or with new message), send mail
      to all members of the nosy list.

    * For new issues, and only for new issue, send mail to
      db.config.detectors['TRIAGE_EMAIL']

    """

    sendto = []

    # The busybody addresses always get mail.
    try:
        sendto += db.config.detectors['BUSYBODY_EMAIL'].split(",")
    except KeyError:
        pass

    # New submission? 
    if None == oldvalues:
        changenote = cl.generateCreateNote(nodeid)
        try:
            # Add triage addresses
            sendto += db.config.detectors['TRIAGE_EMAIL'].split(",")
        except KeyError:
            pass
        oldfiles = []
    else:
        changenote = cl.generateChangeNote(nodeid, oldvalues)
        oldfiles = oldvalues.get('files', [])        

    newfiles = db.issue.get(nodeid, 'files', [])
    if oldfiles != newfiles:
        added = [fid for fid in newfiles if fid not in oldfiles]
        removed = [fid for fid in oldfiles if fid not in newfiles]
        filemsg = ""

        for fid in added:
            url = db.config.TRACKER_WEB + "file%s/%s" % \
                  (fid, db.file.get(fid, "name"))
            changenote+="\nAdded file: %s" % url
        for fid in removed:
            url = db.config.TRACKER_WEB + "file%s/%s" % \
                  (fid, db.file.get(fid, "name"))            
            changenote+="\nRemoved file: %s" % url


    authid = db.getuid()

    new_messages = determineNewMessages(cl, nodeid, oldvalues)

    # Make sure we send a nosy mail even for property-only
    # changes. 
    if not new_messages:
        new_messages = [None]

    for msgid in [msgid for msgid in new_messages if not is_spam(db, msgid)]:
        try:
            if sendto:
                cl.send_message(nodeid, msgid, changenote, sendto,
                            authid=authid)
            nosymessage(db, nodeid, msgid, oldvalues, changenote)
        except roundupdb.MessageSendError, message:
            raise roundupdb.DetectorError, message

def nosymessage(db, nodeid, msgid, oldvalues, note,
                whichnosy='nosy',
                from_address=None, cc=[], bcc=[]):
    """Send a message to the members of an issue's nosy list.

    The message is sent only to users on the nosy list who are not
    already on the "recipients" list for the message.

    These users are then added to the message's "recipients" list.

    If 'msgid' is None, the message gets sent only to the nosy
    list, and it's called a 'System Message'.

    The "cc" argument indicates additional recipients to send the
    message to that may not be specified in the message's recipients
    list.

    The "bcc" argument also indicates additional recipients to send the
    message to that may not be specified in the message's recipients
    list. These recipients will not be included in the To: or Cc:
    address lists.
    """
    if msgid:
        authid = db.msg.get(msgid, 'author')
        recipients = db.msg.get(msgid, 'recipients', [])
    else:
        # "system message"
        authid = None
        recipients = []

    sendto = []
    bcc_sendto = []
    seen_message = {}
    for recipient in recipients:
        seen_message[recipient] = 1

    def add_recipient(userid, to):
        # make sure they have an address
        address = db.user.get(userid, 'address')
        if address:
            to.append(address)
            recipients.append(userid)

    def good_recipient(userid):
        # Make sure we don't send mail to either the anonymous
        # user or a user who has already seen the message.
        return (userid and
                (db.user.get(userid, 'username') != 'anonymous') and
                not seen_message.has_key(userid))

    # possibly send the message to the author, as long as they aren't
    # anonymous
    if (good_recipient(authid) and
        (db.config.MESSAGES_TO_AUTHOR == 'yes' or
         (db.config.MESSAGES_TO_AUTHOR == 'new' and not oldvalues))):
        add_recipient(authid, sendto)

    if authid:
        seen_message[authid] = 1

    # now deal with the nosy and cc people who weren't recipients.
    for userid in cc + db.issue.get(nodeid, whichnosy):
        if good_recipient(userid):
            add_recipient(userid, sendto)

    # now deal with bcc people.
    for userid in bcc:
        if good_recipient(userid):
            add_recipient(userid, bcc_sendto)

    # If we have new recipients, update the message's recipients
    # and send the mail.
    if sendto or bcc_sendto:
        if msgid is not None:
            db.msg.set(msgid, recipients=recipients)
        db.issue.send_message(nodeid, msgid, note, sendto, from_address,
                              bcc_sendto)


def init(db):
    db.issue.react('set', sendmail)
    db.issue.react('create', sendmail)
