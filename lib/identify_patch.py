#!/usr/bin/python
import subprocess, re, sys
from xml.etree import ElementTree

def identify(db, patch):
    """Return revision number and branch of a patch;
    either value may become None."""
    m = re.search(r'---.* ([0-9]+)\)', patch)
    if not m:
        return None
    rev = int(m.group(1))
    return rev

def find_branch(db, rev):
    """Return the branch name for a given revision, or None."""
    c = db.cursor
    c.execute('select branch from svnbranch where rev=%s', (rev,))
    branch = c.fetchone()
    if branch:
        return branch[0]
    # may need to cache more revisions
    return fill_revs(db, lookfor=rev)

def addfiles(cursor, files):
    """Add all files to fileprefix that aren't there, in all
    prefix/suffix combinations."""
    to_add = []
    for f in files:
        cursor.execute("select count(*) from fileprefix "
                       "where prefix='' and suffix=%s",
                       (f,))
        if cursor.fetchone()[0] > 0:
            continue
        parts = f.split('/')
        for i in range(len(parts)):
            prefix = '/'.join(parts[:i])
            if i:
                prefix += '/'
            suffix = '/'.join(parts[i:])
            to_add.append((prefix, suffix))
    cursor.executemany("insert into fileprefix(prefix, suffix) "
                       "values(%s, %s)", to_add)

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
    files = set()
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
            if branch in ('/trunk', '/branches/py3k'):
                # Add all files that ever existed on the main trunks
                for p in paths:
                    files.add(p[len(ppath)+1:])
            c.execute('insert into svnbranch(rev, branch) values(%s, %s)',
                      (rev, branch))
            if lookfor == rev:
                result = branch
    addfiles(c, files)
    db.commit()
    return result

# this runs as a cron job every 30min
if __name__=='__main__':
    # manual setup:
    # create table svnbranch(rev integer primary key, branch text);
    # create table fileprefix(prefix text, suffix text);
    # create index fileprefix_suffix on fileprefix(suffix);
    # then run this once in the instance directory
    sys.path.append('/home/roundup/lib/python2.5/site-packages')
    import roundup.instance
    tracker = roundup.instance.open('.')
    db = tracker.open('admin')
    #db.cursor.execute('delete from svnbranch')
    fill_revs(db)
