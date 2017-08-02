"""
* Sets the 'stage' field to 'resolved' when an issue is closed.
* Sets the 'stage' field to 'patch review' and adds 'patch' to the 'keywords' field.
"""


def issuestates(db, cl, nodeid, newvalues):
    status_change = newvalues.get('status')
    status_close = status_change and status_change == db.status.lookup('closed')

    if status_close:
        if newvalues.get('stage') is None:
            newvalues['stage'] = db.stage.lookup('resolved')

    is_open = cl.get(nodeid, 'status') == db.status.lookup('open')
    patch_keyword = db.keyword.lookup('patch')
    old_keywords = cl.get(nodeid, 'keywords')
    new_keywords = newvalues.get('keywords', [])
    old_prs = cl.get(nodeid, 'pull_requests')
    new_prs = newvalues.get('pull_requests', [])
    pr_change = len(new_prs) > len(old_prs)
    patch_review = db.stage.lookup('patch review')
    needs_change = is_open and pr_change and newvalues.get('stage') != patch_review
    if needs_change:
        newvalues['stage'] = patch_review
        if patch_keyword not in new_keywords and patch_keyword not in old_keywords:
            set_new_keywords = old_keywords[:]
            set_new_keywords.extend(new_keywords)
            set_new_keywords.append(patch_keyword)
            newvalues['keywords'] = set_new_keywords


def init(db):
    db.issue.audit('set', issuestates)
