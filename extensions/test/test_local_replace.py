import sys
import unittest
import os.path

if len(sys.argv) != 2:
    sys.exit('Error: You have to provide the path of Roundup in order to run '
             'the tests (e.g. /opt/tracker-roundup/lib/python2.7/site-packages/).')
# add to sys.path the dir where roundup is installed (local_replace will try
# to import it)
sys.path.append(sys.argv.pop())

testdir = os.path.dirname(os.path.abspath(__file__))
dirs = testdir.split(os.path.sep)
# add the dir where local_replace is (i.e. one level up)
sys.path.append(os.path.sep.join(dirs[:-1]))
# add the dir where the roundup tests are
sys.path.append(os.path.sep.join(dirs[:-3] + ['roundup', 'test']))


from local_replace import PyDevStringHTMLProperty
from test_templating import MockDatabase, TemplatingTestCase


class MockDBItem(object):
    def __init__(self, type):
        self.type = type

    def hasnode(self, id):
        # only issues between 1000 and 2M and prs < 1000 exist in the db
        return ((self.type == 'issue' and 1000 <= int(id) < 2000000) or
                (self.type == 'pull_request' and int(id) < 1000))

    def get(self, id, value, default=None):
        # for issues and prs, the id determines the status:
        #  id%3 == 0: open
        #  id%3 == 1: closed
        #  id%3 == 2: pending/merged
        id = int(id)
        if value == 'title':
            return 'Mock title'
        if value == 'status':
            if self.type == 'issue':
                return id%3
            if self.type == 'pull_request':
                return ['open', 'closed', 'merged'][id%3]
        if self.type == 'status' and value == 'name':
            return ['open', 'closed', 'pending'][id]

    def filter(self, _, filterspec, sort):
        prid = filterspec['number']
        return [prid] if self.hasnode(prid) else []

class PyDevMockDatabase(MockDatabase):
    def __init__(self):
        for type in ['issue', 'msg', 'status', 'pull_request']:
            setattr(self, type, MockDBItem(type))
    def getclass(self, cls):
        return self.issue


class TestPyDevStringHTMLProperty(TemplatingTestCase):
    def test_replacement(self):
        self.maxDiff = None
        # create the db
        self.client.db = self._db = PyDevMockDatabase()
        self.client.db.security.hasPermission = lambda *args, **kw: True
        # the test file contains the text on odd lines and the expected
        # result on even ones, with comments starting with '##'
        f = open(os.path.join(testdir, 'local_replace_data.txt'))
        for text, expected_result in zip(f, f):
            if text.startswith('##') and expected_result.startswith('##'):
                continue  # skip the comments
            p = PyDevStringHTMLProperty(self.client, 'test', '1',
                                        None, 'test', text)
            # decode the str -- Unicode strings have a better diff
            self.assertEqual(p.pydev_hyperlinked().decode(),
                             expected_result.decode())

# run the tests
unittest.main()
