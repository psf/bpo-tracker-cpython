import os, tempfile
from roundup.cgi.actions import Action

class NotChanged(ValueError):
    pass

def download_patch(source, lastrev):
    from mercurial import hg, ui, localrepo, commands, bundlerepo
    UI = ui.ui()
    bundle = tempfile.mktemp(dir="/var/tmp")
    cwd = os.getcwd()
    os.chdir(base)
    try:
    	repo0 = hg.repository(UI,base)
        repo0.ui.quiet=True
        repo0.ui.pushbuffer()
        commands.pull(repo0.ui, repo0, quiet=True)
        repo0.ui.popbuffer() # discard all pull output
        repo0.ui.pushbuffer()
        if commands.incoming(repo0.ui, repo0, source=source, branch=['default'], bundle=bundle, force=False) != 0:
            raise ValueError, "Repository contains no changes"
        rhead = repo0.ui.popbuffer()
        if rhead:
            # output is a list of revisions, one per line. last line should be newest revision
            rhead = rhead.splitlines()[-1].split(':')[1]
        if rhead == lastrev:
            raise NotChanged
        repo=bundlerepo.bundlerepository(UI, ".", bundle)
        repo.ui.pushbuffer()
        commands.diff(repo.ui, repo, rev=['ancestor(.,default)', 'default'])
        result = repo.ui.popbuffer()
    finally:
        os.chdir(cwd)
        if os.path.exists(bundle):
            os.unlink(bundle)
    return result, rhead

class CreatePatch(Action):
    def handle(self):
        db = self.db
        if not self.hasPermission('Create', 'file'):
            raise exceptions.Unauthorised, self._(
                "You do not have permission to create files")
        if self.classname != 'issue':
            raise Reject, "create_patch is only useful for issues"
        if not self.form.has_key('@repo'):
            self.client.error_message.append('hgrepo missing')
            return
        repo = self.form['@repo'].value
        url = db.hgrepo.get(repo, 'url')
        if not url:
            self.client.error_message.append('unknown hgrepo url')
            return
        lastrev = db.hgrepo.get(repo, 'lastrev')
        try:
            diff, head = download_patch(url, lastrev)
        except NotChanged:
            self.client.error_message.append('%s.diff is already available' % lastrev)
            return
        except Exception, e:
            self.client.error_message.append(str(e))
            return
        fileid = db.file.create(name='%s.diff' % head,
                                type='text/plain',
                                content=diff)
        files = db.issue.get(self.nodeid, 'files')
        files.append(fileid)
        db.issue.set(self.nodeid, files=files)
        db.hgrepo.set(repo, lastrev=head)
        self.client.ok_message.append('Successfully downloaded %s.diff' % head)
        db.commit()

def init(instance):
    global base
    base = os.path.join(instance.tracker_home, 'cpython')
    instance.registerAction('create_patch', CreatePatch) 
