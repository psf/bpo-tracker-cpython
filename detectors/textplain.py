# On file creation, if the file is application/octet-stream,
# yet the file content looks like text, change the type to
# text/plain.
def audit_application_octetstream(db, cl, nodeid, newvalues):
    if newvalues.has_key('type') and newvalues['type'] == 'application/octet-stream':
        # check whether this might be a text file
        try:
            text = newvalues['content'].decode('utf-8')
        except UnicodeError:
            return
        # check that there aren't funny control characters in there
        for c in text:
            if ord(c) >= 32:
                continue
            if c not in u' \f\t\r\n':
                return
        newvalues['type'] = 'text/plain'
    

def init(db):
    db.file.audit('create', audit_application_octetstream)
