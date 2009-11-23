import re

substitutions = [ (re.compile(r'\#(?P<ws>\s*)(?P<id>\d+)'),
                   r"<a href='issue\g<id>'>#\g<ws>\g<id></a>" ),
                  (re.compile(r'\brevision(?P<ws>\s*)(?P<revision>\d+)'),
                   r"<a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>revision\g<ws>\g<revision></a>"),
                  (re.compile(r'\brev(?P<ws>\s*)(?P<revision>\d+)'),
                   r"<a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>rev\g<ws>\g<revision></a>"),
                  (re.compile(r'\b(?P<revstr>r|r\s+)(?P<revision>\d+)'),
                   r"<a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>\g<revstr>\g<revision></a>"),
                  (re.compile(r'\b(?P<path>(?:Demo|Doc|Grammar|Include|Lib|Mac|Misc|Modules|Parser|PC|PCbuild|Python|RISCOS|Tools|Objects)/[-.a-zA-Z0-9_/]+[a-zA-Z0-9]/?)'),
                   r'<a href="http://svn.python.org/view/python/trunk/\g<path>">\g<path></a>'),
                   ]

def localReplace(message):

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
    print " revision 222", localReplace(" revision 222")
    print " wordthatendswithr 222", localReplace(" wordthatendswithr 222")
    print " r222", localReplace(" r222")
    print " r 222", localReplace(" r 222")
    print " #555", localReplace(" #555")

