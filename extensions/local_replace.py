import re
import cgi
from roundup import hyperdb
from roundup.cgi.templating import register_propclass, StringHTMLProperty


# pre-hg migration
'''
substitutions = [
    #  r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
    (re.compile(r'\b(?<![/?&;])(?P<revstr>r(ev(ision)?)?\s*)(?P<revision>\d+)'),
     r'<a href="https://svn.python.org/view?rev=\g<revision>'
     r'&view=rev">\g<revstr>\g<revision></a>'),

    # Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
    (re.compile(r'(?P<sep>(?<!\w/)|(?<!\w)/)(?P<path>(?:Demo|Doc|Grammar|'
                r'Include|Lib|Mac|Misc|Modules|Parser|PC|PCbuild|Python|'
                'RISCOS|Tools|Objects)/[-.a-zA-Z0-9_/]+[a-zA-Z0-9]/?)'),
     r'<a href="https://svn.python.org/view/python/branches/'
     r'py3k/\g<path>">\g<sep>\g<path></a>'),
]
'''


def make_file_link(match):
    """Convert files to links to the GitHub repo."""
    baseurl = 'https://github.com/python/cpython/blob/'
    branch = match.group('v') or 'master/'  # the match includes the '/'
    path = match.group('path')
    lnum = match.group('lnum') or ''  # the match includes the ':'
    url = baseurl + branch + path
    if not path.endswith('/'):
        # files without and with line number
        if not lnum:
            return '<a href="%s">%s</a>' % (url, path)
        else:
            return '<a href="%s#L%s">%s%s</a>' % (url, lnum[1:], path, lnum)
    else:
        # dirs
        return '<a href="%s">%s</a>%s' % (url, path, lnum)


def guess_version(path):
    """Search for Python version hints in the file path."""
    match = re.search(r'((?<=[Pp]ython)[23]\d\d?|[23]\.\d\d?)', path)
    if not match:
        return 'main'
    version = match.group(1)
    if '.' not in version:
        version = '.'.join((version[0], version[1:]))
    return version


def make_traceback_link(match):
    """Convert the file/line in the traceback lines in a link."""
    baseurl = 'https://github.com/python/cpython/blob/'
    path = match.group('path')  # first part of the path
    branch = guess_version(match.group('fullpath'))  # guessed branch
    file = match.group('file')  # second part after Lib/
    nfile = file.replace('\\', '/')  # normalize the path separators
    lnum = match.group('lnum')
    return ('File "%s<a href="%s%s/Lib/%s#L%s">%s</a>", line %s' %
            (path, baseurl, branch, nfile, lnum, file, lnum))

def make_pep_link(match):
    text = match.group(0)
    pepnum = match.group(1).zfill(4)
    return '<a href="https://www.python.org/dev/peps/pep-%s/">%s</a>' % (pepnum, text)


# these regexs have test in tests/test_local_replace.py

seps = r'\b(?<![-/?&;=_:#])'  # these chars should not precede the targets
substitutions = [
    # deadbeeffeed  (hg hashes with exactly twelve or forty chars,
    # git has 10 or more as it grows as time goes on)
    (re.compile(r'%s(?P<revision>(git|hg)?[a-fA-F0-9]{40})\b' % seps),
     r'<a href="https://hg.python.org/lookup/\g<revision>">\g<revision></a>'),
    (re.compile(r'%s(?P<revision>(git|hg)?[a-fA-F0-9]{10,12})\b' % seps),
     r'<a href="https://hg.python.org/lookup/\g<revision>">\g<revision></a>'),

    # r12345, r 12345, rev12345, rev. 12345, revision12345, revision 12345
    (re.compile(r'%s(?P<revstr>r\.?(ev\.?(ision)?)?\s*)(?P<revision>\d{4,})' % seps),
     r'<a href="https://hg.python.org/lookup/r\g<revision>">\g<revstr>\g<revision></a>'),

    # Lib/somefile.py, Lib/somefile.py:123, Modules/somemodule.c:123, ...
    (re.compile(r'%s(?P<v>2\.[0-7]/|3\.\d/)?(?P<path>(?:Demo|Doc|Grammar|'
                r'Include|Lib|Mac|Misc|Modules|Parser|PC|PCbuild|Python|'
                r'RISCOS|Tools|Programs|Objects)/'
                r'[-.\w/]+[a-zA-Z0-9]/?)(?P<lnum>:\d{1,5})?' % seps),
     make_file_link),

    # traceback lines: File "Lib/somefile.py", line 123 in some_func
    # note: this regex is not 100% accurate, it might get the wrong part of
    # the path or link to non-existing files, but it usually works fine
    (re.compile(r'File "(?P<fullpath>(?P<path>[-.\w/\\:]+(?<!var)[/\\][Ll]ib[/\\]'
                r'(?!.*site-packages)(python[\d.]*[/\\])?)(?P<file>[-.\w/\\]+?\.py))", '
                r'line (?P<lnum>\d{1,5})'),
     make_traceback_link),

    # PEP 8, PEP8, PEP 0008, ...
    (re.compile(r'%s\b(?<![/=-])PEP\s*(\d{1,4})(?!/)\b' % seps, re.I),
     make_pep_link),

    # devguide
    (re.compile(r'%s(devguide((?:/\w+(.html)?(#[\w-]+)?)?)?)' % seps),
     r'<a href="https://devguide.python.org\2">\1</a>'),
]


# if the issue number is too big the db will explode -- limit it to 7 digits
issue_re = re.compile(r'(?P<text>((?<!\w)\#|\b(?<![-/_])(issue|bpo-))'
                      r'\s*(?P<id>1?\d{1,6}))\b', re.I)

# PR number, pull request number, pullrequest number
pullrequest_re = re.compile(r'(?P<text>(\b(?<![-/_])(PR-?|GH-?|pull\s*request))\s*'
                            r'(?P<pr_no>\d+))\b', re.I)


class PyDevStringHTMLProperty(StringHTMLProperty):
    def _hyper_repl(self, match):
        """
        Override the original method and change it to still linkify URLs and
        emails but avoid linkification of issues and other items
        (except messages and files).
        """
        if match.group('url'):
            return self._hyper_repl_url(match, '<a href="%s">%s</a>%s')
        elif match.group('email'):
            return self._hyper_repl_email(match, '<a href="mailto:%s">%s</a>')
        elif (len(match.group('id')) < 10 and
              match.group('class') and
              match.group('class').lower() in ('msg', 'file')):
            # linkify msgs but not issues and other things
            return self._hyper_repl_item(match,
                '<a href="%(cls)s%(id)s">%(item)s</a>')
        else:
            # just return the matched text
            return match.group(0)

    def pydev_hyperlinked(self):
        """Create python-dev-specific links."""
        # first do the normal linkification (without linkify the issues)
        message =  self.plain(hyperlink=1)
        # then add links for revision numbers and paths
        for cre, replacement in substitutions:
            message = cre.sub(replacement, message)
        # finally add links for issues
        message = issue_re.sub(self._linkify_issue, message)
        message = pullrequest_re.sub(self._linkify_pull_request, message)
        return message

    def _linkify_issue(self, match):
        """Turn an issue (e.g. 'issue 1234' or '#1234') to an HTML link"""
        template = ('<a class="%(status)s" title="[%(status)s] %(title)s" '
                    'href="issue%(issue_id)s">%(text)s</a>')
        issue_id = match.group('id')
        text = match.group('text')
        cl = self._db.issue
        # check if the issue exists
        if not cl.hasnode(issue_id):
            return text
        # get the title
        title = cgi.escape(cl.get(issue_id, 'title').replace('"', "'"))
        status_id = cl.get(issue_id, 'status')
        # get the name of the status
        if status_id is not None:
            status = self._db.status.get(status_id, 'name')
        else:
            status = 'none'
        return template % dict(issue_id=issue_id, title=title,
                               status=status, text=text)

    def _linkify_pull_request(self, match):
        """Turn a pullrequest (e.g. 'PR 123') to an HTML link"""
        template = ('<a href="%(base_url)s%(pr_no)s" %(cls)s'
                    'title="GitHub PR %(pr_no)s%(info)s">%(text)s</a>')
        pr_no = match.group('pr_no')
        text = match.group('text')
        # find title and status
        cl = self._db.pull_request
        # find all the pull_request that refer to GitHub PR pr_no,
        # with the most recently updated first
        pr_ids = cl.filter(None, dict(number=pr_no), sort=[('-', 'activity')])
        title = status = info = cls = ''
        for pr_id in pr_ids:
            if not title:
                title = cl.get(pr_id, 'title', '')
            if not status:
                status = cl.get(pr_id, 'status', '')
            if title and status:
                # once we get both, escape and add to info
                status = cgi.escape(status).replace('"', "'")
                title = cgi.escape(title).replace('"', "'")
                info = ': [%s] %s' % (status, title)
                break
        if status:
            cls = 'class="%s" ' % ('open' if status == 'open' else 'closed')
        base_url = 'https://github.com/python/cpython/pull/'
        return template % dict(base_url=base_url, pr_no=pr_no, cls=cls,
                               info=info, text=text)


noise_changes = re.compile('(nosy_count|message_count)\: \d+\.0( -> \d+\.0)?')

def clean_count(history):
    history = noise_changes.sub('', history).replace('<td><br />', '<td>')
    return history

def init(instance):
    register_propclass(hyperdb.String, PyDevStringHTMLProperty)
    instance.registerUtil('clean_count', clean_count)
