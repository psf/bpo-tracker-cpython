import re

substitutions = [
    #  #1234, # 1234
    (re.compile(r'\#(?P<ws>\s*)(?P<id>1?\d{4,6})\b'),
     r'<a href="issue\g<id>">#\g<ws>\g<id></a>'),
    #  r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
    (re.compile(r'\b(?<!/)(?P<revstr>r(ev(ision)?)?\s*)(?P<revision>\d+)'),
     r'<a href="http://svn.python.org/view?rev=\g<revision>&view=rev">\g<revstr>\g<revision></a>'),
    # Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
    (re.compile(r'(?P<sep>(?<!\w/)|(?<!\w)/)(?P<path>(?:Demo|Doc|Grammar|Include|Lib|Mac|Misc|'
                r'Modules|Parser|PC|PCbuild|Python|RISCOS|Tools|Objects)/[-.a-zA-Z0-9_/]+[a-zA-Z0-9]/?)'),
     r'<a href="http://svn.python.org/view/python/trunk/\g<path>">\g<sep>\g<path></a>'),
]

def localReplace(message):
    """
    Turn the following strings in HTML links:
    #1234, # 1234  ->  <a href="issue1234">#1234</a>
    r12345, r 12345, rev12345, rev 12345, revision12345, revision 12345
        ->  <a href="http://svn.python.org/view?rev=12345&view=rev">r12345</a>
    Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
        ->  <a href="http://svn.python.org/view/python/trunk/Dir/filename.ext">Dir/filename.ext</a>
    """
    for cre, replacement in substitutions:
        message = cre.sub(replacement, message)

    return message

noise_change = re.compile('(nosy_count|message_count)\: \d+\.0 -> \d+\.0')
noise_init = re.compile('(nosy_count|message_count)\: \d+\.0')
br = re.compile('<td><br />')

def clean_count(history):
    history = noise_change.sub('', history)
    history = noise_init.sub('', history)
    history = br.sub('<td>', history)
    return history

def init(instance):
    instance.registerUtil('localReplace', localReplace)
    instance.registerUtil('clean_count', clean_count)

if "__main__" == __name__:
    import unittest

    class TestLocalReplace(unittest.TestCase):
        def test_localReplace(self):
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
                ('http://svn.python.org/view/python/tags/r265 ',
                 'http://svn.python.org/view/python/tags/r265 '),

                ##  #1234, # 1234
                ## the lowest issue id is #1000, the highest is #1779871
                (' #1 ', ' #1 '),
                (' #10 ', ' #10 '),
                (' #999 ', ' #999 '),
                (' # 999 ', ' # 999 '),
                ('#1000 ', '<a href="issue1000">#1000</a> '),
                (' #1000 ', ' <a href="issue1000">#1000</a> '),
                (' # 1000 ', ' <a href="issue1000"># 1000</a> '),
                (' #5555 ', ' <a href="issue5555">#5555</a> '),
                (' # 5555 ', ' <a href="issue5555"># 5555</a> '),
                (' #555555 ', ' <a href="issue555555">#555555</a> '),
                (' # 555555 ', ' <a href="issue555555"># 555555</a> '),
                (' #1999999 ', ' <a href="issue1999999">#1999999</a> '),
                (' # 1999999 ', ' <a href="issue1999999"># 1999999</a> '),
                (' #2000000 ', ' #2000000 '),
                (' # 2000000 ', ' # 2000000 '),

                ## Lib/somefile.py, Modules/somemodule.c, Doc/somedocfile.rst, ...
                ('Lib/cgi.py',
                 '<a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">Lib/cgi.py</a>'),
                ('/Lib/cgi.py',
                 '<a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">/Lib/cgi.py</a>'),
                ('the bug is in Lib/cgi.py.',
                 'the bug is in <a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">Lib/cgi.py</a>.'),
                ('the bug is in /Lib/cgi.py.',
                 'the bug is in <a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">/Lib/cgi.py</a>.'),
                ('(Lib/cgi.py)',
                 '(<a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">Lib/cgi.py</a>)'),
                ('(/Lib/cgi.py)',
                 '(<a href="http://svn.python.org/view/python/trunk/Lib/cgi.py">/Lib/cgi.py</a>)'),
                ('http://svn.python.org/view/python/tags/r265/Lib/cgi.py',
                 'http://svn.python.org/view/python/tags/r265/Lib/cgi.py'),
                ('http://svn.python.org/view/python/tags/r265/Lib/cgi.py?view=markup',
                 'http://svn.python.org/view/python/tags/r265/Lib/cgi.py?view=markup'),
            ]
            for text, expected_result in test_strings:
                self.assertEqual(expected_result, localReplace(text))

    # run the tests when executed directly
    unittest.main()
