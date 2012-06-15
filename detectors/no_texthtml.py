
def audit_html_files(db, cl, nodeid, newvalues):
    if newvalues.has_key('type') and newvalues['type'] in ('text/html', 'html', 'text/x-html'):
        newvalues['type'] = 'text/plain'


def init(db):
    db.file.audit('set', audit_html_files)
    db.file.audit('create', audit_html_files)
