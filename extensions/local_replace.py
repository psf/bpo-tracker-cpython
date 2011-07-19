import re
import cgi
from roundup import hyperdb
from roundup.cgi.templating import register_propclass, StringHTMLProperty


# pre-hg migration
'''
substitutions = [
    #  r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
    (re.compile(r'\b(?<![/?&;])(?P<revstr>r(ev(ision)?)?\s*)(?P<revision>\d+)'),
     r'<a href="http://svn.python.org/view?rev=\g<revision>'
     r'&view=rev">\g<revstr>\g<revision></a>'),

    # Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
    (re.compile(r'(?P<sep>(?<!\w/)|(?<!\w)/)(?P<path>(?:Demo|Doc|Grammar|'
                r'Include|Lib|Mac|Misc|Modules|Parser|PC|PCbuild|Python|'
                'RISCOS|Tools|Objects)/[-.a-zA-Z0-9_/]+[a-zA-Z0-9]/?)'),
     r'<a href="http://svn.python.org/view/python/branches/'
     r'py3k/\g<path>">\g<sep>\g<path></a>'),
]
'''


def make_file_link(match):
    baseurl = 'http://hg.python.org/cpython/file/default/'
    sep = match.group('sep')
    path = match.group('path')
    npath = path.replace('\\', '/')  # normalize the path separators
    lnum = match.group('lnum') or ''  # the match includes the ':'
    if not npath.endswith('/'):
        # files without and with line number
        if not lnum:
            return '<a href="%s%s">%s%s</a>' % (baseurl, npath, sep, path)
        else:
            return '<a href="%s%s#l%s">%s%s%s</a>' % (baseurl, npath, lnum[1:],
                                                      sep, path, lnum)
    else:
        # dirs
        return '<a href="%s%s">%s%s</a>%s' % (baseurl, npath, sep, path, lnum)


def guess_version(path):
    """Search for Python version hints in the file path."""
    match = re.search(r'((?<=[Pp]ython)[23]\d|[23]\.\d)', path)
    if not match:
        return 'default'
    version = match.group(1)
    if '.' not in version:
        version = '.'.join(version)
    if version in ['2.5', '2.6', '2.7', '3.1', '3.2']:
        return version
    return 'default'


def make_traceback_link(match):
    """Convert the file/line in the traceback lines in a link."""
    baseurl = 'http://hg.python.org/cpython/file/'
    path = match.group('path')  # first part of the path
    branch = guess_version(match.group('fullpath'))  # guessed branch
    file = match.group('file')  # second part after Lib/
    nfile = file.replace('\\', '/')  # normalize the path separators
    lnum = match.group('lnum')
    return ('File "%s<a href="%s%s/Lib/%s#l%s">%s</a>", line %s' %
            (path, baseurl, branch, nfile, lnum, file, lnum))

def make_pep_link(match):
    text = match.group(0)
    pepnum = match.group(1).zfill(4)
    return '<a href="http://www.python.org/dev/peps/pep-%s/">%s</a>' % (pepnum, text)


# these regexs have test in tests/test_local_replace.py

substitutions = [
    # deadbeeffeed  (hashes with exactly twelve or forty chars)
    (re.compile(r'\b(?<![/?&;])(?P<revision>[a-fA-F0-9]{40})\b'),
     r'<a href="http://hg.python.org/lookup/\g<revision>">\g<revision></a>'),
    (re.compile(r'\b(?<![/?&;])(?P<revision>[a-fA-F0-9]{12})\b'),
     r'<a href="http://hg.python.org/lookup/\g<revision>">\g<revision></a>'),

    # r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
    (re.compile(r'\b(?<![/?&;])(?P<revstr>r(ev(ision)?)?\s*)(?P<revision>\d{4,})'),
     r'<a href="http://hg.python.org/lookup/r\g<revision>">\g<revstr>\g<revision></a>'),

    # Lib/somefile.py, Lib/somefile.py:123, Modules/somemodule.c:123, ...
    (re.compile(r'(?P<sep>(?<!\w/)|(?<!\w)/)(?P<path>(?:Demo|Doc|Grammar|'
                r'Include|Lib|Mac|Misc|Modules|Parser|PC|PCbuild|Python|'
                r'RISCOS|Tools|Objects)/[-.\w/]+[a-zA-Z0-9]/?)(?P<lnum>:\d{1,5})?'),
     make_file_link),

    # traceback lines: File "Lib/somefile.py", line 123 in some_func
    # note: this regex is not 100% accurate, it might get the wrong part of
    # the path or link to non-existing files, but it usually works fine
    (re.compile(r'File "(?P<fullpath>(?P<path>[-.\w/\\:]+(?<!var)[/\\][Ll]ib[/\\]'
                r'(?!.*site-packages)(python[\d.]*[/\\])?)(?P<file>[-.\w/\\]+?\.py))", '
                r'line (?P<lnum>\d{1,5})'),
     make_traceback_link),

    # PEP 8, PEP8, PEP 0008, ...
    (re.compile(r'PEP\s*(\d{1,4})\b', re.I),
     make_pep_link),
]


# if the issue number is too big the db will explode -- limit it to 7 digits
issue_re = re.compile(r'(?P<text>(\#|\b(?<!/)issue)\s*(?P<id>1?\d{1,6}))\b', re.I)


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


noise_changes = re.compile('(nosy_count|message_count)\: \d+\.0( -> \d+\.0)?')

def clean_count(history):
    history = noise_changes.sub('', history).replace('<td><br />', '<td>')
    return history

def init(instance):
    register_propclass(hyperdb.String, PyDevStringHTMLProperty)
    instance.registerUtil('clean_count', clean_count)
