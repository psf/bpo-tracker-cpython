import sys
import unittest
import os.path

if len(sys.argv) != 2:
    sys.exit('Error: You have to provide the path of Roundup in order to run '
             'the tests (e.g. /opt/tracker-roundup/lib/python2.6/site-packages/).')
# add to sys.path the dir where roundup is installed (local_replace will try
# to import it)
sys.path.append(sys.argv.pop())

dirs = os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)
# add the dir where local_replace is (i.e. one level up)
sys.path.append(os.path.sep.join(dirs[:-1]))
# add the dir where the roundup tests are
sys.path.append(os.path.sep.join(dirs[:-4] + ['roundup-src', 'test']))


from local_replace import PyDevStringHTMLProperty
from test_templating import MockDatabase, TemplatingTestCase


class MockDBItem(object):
    def __init__(self, values):
        # *values* is a list of ids that are supposed to exist in the db
        # (note that there's no difference here between issues, msg, etc.)
        self.ids = map(str, values)

    def hasnode(self, id):
        return id in self.ids

    def get(self, id, value):
        if value == 'title':
            return 'Mock title'
        if value == 'status':
            return 1
        if value == 'name':
            return 'open'

class PyDevMockDatabase(MockDatabase):
    def __init__(self, values):
        self.issue = self.msg = self.status = MockDBItem(values)
    def getclass(self, cls):
        return self.issue


test_strings = [
    ## r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
    ('r222 ',
     '<a href="http://svn.python.org/view?rev=222&view=rev">r222</a> '),
    (' r222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">r222</a> '),
    (' r 222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">r 222</a> '),
    (' rev222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">rev222</a> '),
    (' rev  222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">rev  222</a> '),
    (' revision222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">revision222</a> '),
    (' revision 222 ',
     ' <a href="http://svn.python.org/view?rev=222&view=rev">revision 222</a> '),
    ('wordthatendswithr 222',
     'wordthatendswithr 222'),


    ##  #1234, # 1234
    ## the lowest issue id on bugs.python.org is #1000, the highest is #1779871
    (' #1 ', ' #1 '),
    (' #10 ', ' #10 '),
    (' #999 ', ' #999 '),
    (' # 999 ', ' # 999 '),
    ('#1000 ',
     '<a class="open" title="[open] Mock title" href="issue1000">#1000</a> '),
    (' #1000 ',
     ' <a class="open" title="[open] Mock title" href="issue1000">#1000</a> '),
    (' # 1000 ',
     ' <a class="open" title="[open] Mock title" href="issue1000"># 1000</a> '),
    (' #5555 ',
     ' <a class="open" title="[open] Mock title" href="issue5555">#5555</a> '),
    (' # 5555 ',
     ' <a class="open" title="[open] Mock title" href="issue5555"># 5555</a> '),
    (' #555555 ',
     ' <a class="open" title="[open] Mock title" href="issue555555">#555555</a> '),
    (' # 555555 ',
     ' <a class="open" title="[open] Mock title" href="issue555555"># 555555</a> '),
    (' #1999999 ',
     ' <a class="open" title="[open] Mock title" href="issue1999999">#1999999</a> '),
    (' # 1999999 ',
     ' <a class="open" title="[open] Mock title" href="issue1999999"># 1999999</a> '),
    (' #1020 ', ' #1020 '),
    (' #2000000 ', ' #2000000 '),
    (' # 2000000 ', ' # 2000000 '),
    (' #1234567890123  ', ' #1234567890123  '),
    ('pyissue1000', 'pyissue1000'),

    ## Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
    ('Lib/cgi.py',
     '<a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">Lib/cgi.py</a>'),
    ('/Lib/cgi.py',
     '<a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">/Lib/cgi.py</a>'),
    ('see Lib/cgi.py.',
     'see <a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">Lib/cgi.py</a>.'),
    ('see /Lib/cgi.py.',
     'see <a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">/Lib/cgi.py</a>.'),
    ('(Lib/cgi.py)',
     '(<a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">Lib/cgi.py</a>)'),
    ('(/Lib/cgi.py)',
     '(<a href="http://svn.python.org/view/python/branches/py3k/Lib/cgi.py">/Lib/cgi.py</a>)'),

    ## URLs
    ('http://svn.python.org/view/python/tags/r265 ',
     ('<a href="http://svn.python.org/view/python/tags/r265">'
      'http://svn.python.org/view/python/tags/r265</a> ')),
    ('http://svn.python.org/view/python/tags/r265/Lib/cgi.py',
     ('<a href="http://svn.python.org/view/python/tags/r265/Lib/cgi.py">'
      'http://svn.python.org/view/python/tags/r265/Lib/cgi.py</a>')),
    ('http://svn.python.org/view/python/tags/r265/Lib/cgi.py?view=markup',
     ('<a href="http://svn.python.org/view/python/tags/r265/Lib/cgi.py?view=markup">'
      'http://svn.python.org/view/python/tags/r265/Lib/cgi.py?view=markup</a>')),
    ('http://bugs.python.org/issue1000',
     '<a href="http://bugs.python.org/issue1000">http://bugs.python.org/issue1000</a>'),
    ('http://svn.python.org/view/python/branches/release26-maint'
     '/Lib/socket.py?r1=83624&r2=83623&pathrev=83624',
     '<a href="http://svn.python.org/view/python/branches/release26-maint/'
     'Lib/socket.py?r1=83624&amp;r2=83623&amp;pathrev=83624">http://svn.python.org/'
     'view/python/branches/release26-maint/Lib/socket.py'
     '?r1=83624&amp;r2=83623&amp;pathrev=83624</a>'),

    ## emails
    ('fixed@europython.eu',
     '<a href="mailto:fixed@europython.eu">fixed@europython.eu</a>'),
    ('<fixed@europython.eu>',
     '&lt;<a href="mailto:fixed@europython.eu">fixed@europython.eu</a>&gt;'),

    ## items
    ('see msg1000.', 'see <a href="msg1000">msg1000</a>.'),
    ('see msg 1000.', 'see <a href="msg1000">msg 1000</a>.'),
    ('see file1000.', 'see <a href="file1000">file1000</a>.'),
    ('see file 1000.', 'see <a href="file1000">file 1000</a>.'),
    # only msgs and files are linkified
    ('see version1000.', 'see version1000.'),
    ('see version 1000.', 'see version 1000.'),
]


class TestPyDevStringHTMLProperty(TemplatingTestCase):
    def test_replacement(self):
        # create a db with a few issue/msg/file ids
        self.client.db = self._db = PyDevMockDatabase(
                [1000, 5555, 555555, 1999999, 2000000, 1234567890123])
        self.client.db.security.hasPermission = lambda *args, **kw: True
        for text, expected_result in test_strings:
            p = PyDevStringHTMLProperty(self.client, 'test', '1',
                                        None, 'test', text)
            self.assertEqual(expected_result, p.pydev_hyperlinked())

# run the tests
unittest.main()
