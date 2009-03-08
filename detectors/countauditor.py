
def count_nosy_msg(db, cl, nodeid, newvalues):
    ''' Update the counts of messages and nosy users on issue edit'''
    if 'nosy' in newvalues:
            newvalues['nosy_count'] = len(set(newvalues['nosy']))
    if 'messages' in newvalues:
        newvalues['message_count'] = len(set(newvalues['messages']))


def init(db):
    # Should run after the creator and auto-assignee are added
    db.issue.audit('create', count_nosy_msg, priority=120)
    db.issue.audit('set', count_nosy_msg, priority=120)
