#
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
# This module is free software, and you may redistribute it and/or modify
# under the same terms as Python, so long as this copyright message and
# disclaimer are retained in their original form.
#
# IN NO EVENT SHALL BIZAR SOFTWARE PTY LTD BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING
# OUT OF THE USE OF THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# BIZAR SOFTWARE PTY LTD SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS"
# BASIS, AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
# 
# Modified from nosyreaction by P. Dubois to send mail to a busybody list
# that wants to know about EVERY change.

import sets

from roundup import roundupdb, hyperdb

def busyreaction(db, cl, nodeid, oldvalues):
    ''' busybody mail
    '''
    try:
        sendto = db.config.detectors['BUSYBODY_EMAIL'].split()
    except KeyError:
        return

    msgIDS = determineNewMessages(cl, nodeid, oldvalues)
    if oldvalues is None: # a create
        note = cl.generateCreateNote(nodeid)
    else:
        note = cl.generateChangeNote(nodeid, oldvalues)

    for msgid in msgIDS:
        try:
            cl.send_message(nodeid, msgid, note, sendto)
        except roundupdb.MessageSendError, message:
            raise roundupdb.DetectorError, message
    if not msgIDS:
        try:
            cl.send_message(nodeid, None, note, sendto)
        except roundupdb.MessageSendError, message:
            raise roundupdb.DetectorError, message


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

def init(db):
    db.issue.react('create', busyreaction)
    db.issue.react('set', busyreaction)

# vim: set filetype=python ts=4 sw=4 et si
