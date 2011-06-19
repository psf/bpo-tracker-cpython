# Auditor for hgrepo records
# Split repo#branch URLs in repo and branch

def hgsplit(db, cl, nodeid, newvalues):
    url = newvalues.get('url','')
    if '#' in url:
        url, branch = url.split('#', 1)
        newvalues['url'] = url
        newvalues['patchbranch'] = branch

def init(db):
    db.hgrepo.audit('create', hgsplit)
