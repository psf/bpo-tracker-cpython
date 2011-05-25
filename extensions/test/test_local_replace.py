import sys
import unittest
import os.path

if len(sys.argv) != 2:
    sys.exit('Error: You have to provide the path of Roundup in order to run '
             'the tests (e.g. /opt/tracker-roundup/lib/python2.6/site-packages/).')
# add to sys.path the dir where roundup is installed (local_replace will try
# to import it)
sys.path.append(sys.argv.pop())

testdir = os.path.dirname(os.path.abspath(__file__))
dirs = testdir.split(os.path.sep)
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


class TestPyDevStringHTMLProperty(TemplatingTestCase):
    def test_replacement(self):
        # create a db with a few issue/msg/file ids
        self.client.db = self._db = PyDevMockDatabase(
                [1000, 5555, 555555, 1999999, 2000000, 1234567890123])
        self.client.db.security.hasPermission = lambda *args, **kw: True
        # the test file contains the text on odd lines and the expected
        # result on even ones, with comments starting with '##'
        f = open(os.path.join(testdir, 'local_replace_data.txt'))
        for text, expected_result in zip(f, f):
            if text.startswith('##') and expected_result.startswith('##'):
                continue  # skip the comments
            p = PyDevStringHTMLProperty(self.client, 'test', '1',
                                        None, 'test', text)
            self.assertEqual(p.pydev_hyperlinked(), expected_result)

# run the tests
unittest.main()
