# Auditor for GitHub URLs
# Check if it is a valid GitHub Pull Request URL and extract PR number

import re


repo_number_re = re.compile(r'^#?(?P<number>\d+)$')
url_re = re.compile(r'(https?:\\)?github\.com/python/cpython/pull/(?P<number>\d+)')

def validate_pr_uniqueness(db, cl, nodeid, newvalues):
    """
    Verifies if newly added PR isn't already attached to an issue.
    This process is a 2-level action, first a pull_request object is created, which
    goes through validate_pr_number to extract the PR number in case an URL is passed,
    only then we validate PR uniqueness within a single issue.
    """
    newprs = set(newvalues.get('pull_requests',()))
    if not newprs:
        return
    oldprs = set()
    if nodeid:
        # if this is an existing issue, get the list of existing prs
        oldprs = set(db.issue.get(nodeid, 'pull_requests'))
        newprs -= oldprs
    try:
        # get the newly created PR number
        number = db.pull_request.get(newprs.pop(), 'number')
    except KeyError:
        return
    # and compare with those already attached to an issue
    for oldpr in oldprs:
        oldnumber = db.pull_request.get(oldpr, 'number')
        if number == oldnumber:
            raise ValueError("GitHub PR already added to issue")

def validate_pr_number(db, cl, nodeid, newvalues):
    try:
        number = extract_number(newvalues['number'])
        if number:
            newvalues['number'] = number
    except KeyError:
        pass

def extract_number(input):
    """
    Extracts PR number from the following forms:
    - #number
    - number
    - full url
    and returns its number.
    """
    # try matching just the number
    repo_number_match = repo_number_re.search(input)
    if repo_number_match:
        return repo_number_match.group('number')
    # fallback to parsing the entire url
    url_match = url_re.search(input)
    if url_match:
        return url_match.group('number')
    # if nothing else raise error
    raise ValueError("Unknown PR format, acceptable formats are: "
                     "full github URL, #pr_number, pr_number")


def init(db):
    db.issue.audit('create', validate_pr_uniqueness)
    db.issue.audit('set', validate_pr_uniqueness)
    db.pull_request.audit('create', validate_pr_number)
    db.pull_request.audit('set', validate_pr_number)
