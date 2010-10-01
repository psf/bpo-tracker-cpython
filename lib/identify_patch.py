import subprocess
from xml.etree import ElementTree

def find_branch(db, rev):
    c = db.cursor
    c.execute('select branch from svnbranch where rev=%s', (rev,))
    branch = c.fetchone()
    if branch:
        return branch[0]
    # may need to cache more revisions
    return fill_revs(db, lookfor=rev)

def fill_revs(db, lookfor=None):
    result = None
    c = db.cursor
    c.execute('select max(rev) from svnbranch')
    start = c.fetchone()[0]
    if not start:
        start = 1
    else:
        start = start+1
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

if __name__=='__main__':
    # manual setup:
    # create table svnbranch(rev integer primary key, branch text);
    # then run this once in the instance directory
    import roundup.instance
    tracker = roundup.instance.open('.')
    db = tracker.open('admin')
    fill_revs(db)
