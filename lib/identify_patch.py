#!/usr/bin/python
import subprocess, re, sys
from xml.etree import ElementTree

def identify(db, patch):
    """Return revision number and branch of a patch;
    either value may become None."""
    m = re.search('---.* ([0-9]+)', patch)
    if not m:
        return None, None
    rev = int(m.group(1))
    return rev, find_branch(db, rev)

def find_branch(db, rev):
    """Return the branch name for a given revision, or None."""
    c = db.cursor
    c.execute('select branch from svnbranch where rev=%s', (rev,))
    branch = c.fetchone()
    if branch:
        return branch[0]
    # may need to cache more revisions
    return fill_revs(db, lookfor=rev)

def fill_revs(db, lookfor=None):
    """Initialize/update svnbranch table. If lookfor is given,
    return its branch, or None if that cannot be determined."""
    result = None
    c = db.cursor
    c.execute('select max(rev) from svnbranch')
    start = c.fetchone()[0]
    if not start:
        start = 1
    else:
        start = start+1
    if lookfor and lookfor < start:
        # revision is not in database
        return None
    p = subprocess.Popen(['svn', 'log', '-r%s:HEAD' % start, '--xml', '-v',
                          'http://svn.python.org/projects'],
                         stdout = subprocess.PIPE,
                         stderr = open('/dev/null', 'w'))
    data = p.stdout.read()
    if p.wait() != 0:
        # svn log failed
        return None
    xml = ElementTree.fromstring(data)
    for entry in xml.findall('logentry'):
        rev = int(entry.get('revision'))
        paths = [p.text for p in entry.findall('paths/path')]
        if not paths:
            continue
        path = paths[0]
        if (not path.startswith('/python') or 
            # The count may be smaller on the revision that created /python
            # or the branch
            path.count('/')<3):
            continue
        branch = path[len('/python'):]
        if branch.startswith('/trunk'):
            branch = '/trunk'
        else:
            d1, d2 = branch.split('/', 3)[1:3]
            branch = '/'+d1+'/'+d2
        ppath = '/python'+branch
        for p in paths:
            if not p.startswith(ppath):
                # inconsistent commit
                break
        else:
            c.execute('insert into svnbranch(rev, branch) values(%s, %s)',
                      (rev, branch))
            if lookfor == rev:
                result = branch
    db.commit()
    return branch

# this runs as a cron job every 30min
if __name__=='__main__':
    # manual setup:
    # create table svnbranch(rev integer primary key, branch text);
    # then run this once in the instance directory
    sys.path.append('/home/roundup/lib/python2.5/site-packages')
    import roundup.instance
    tracker = roundup.instance.open('.')
    db = tracker.open('admin')
    fill_revs(db)
