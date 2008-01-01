import re

substitutions = [ (re.compile('\#(?P<ws>\s*)(?P<id>\d+)'),
                   "<a href='issue\g<id>'>#\g<ws>\g<id></a>" ),
                  (re.compile('(?P<prews>\s+)revision(?P<ws>\s*)(?P<revision>\d+)'),
                   "\g<prews><a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>revision\g<ws>\g<revision></a>"),
                  (re.compile('(?P<prews>\s+)rev(?P<ws>\s*)(?P<revision>\d+)'),
                   "\g<prews><a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>rev\g<ws>\g<revision></a>"),
                  (re.compile('(?P<prews>\s+)(?P<revstr>r|r\s+)(?P<revision>\d+)'),
                   "\g<prews><a href='http://svn.python.org/view?rev=\g<revision>&view=rev'>\g<revstr>\g<revision></a>"),
                   ]

def localReplace(message):

    for cre, replacement in substitutions:
        message = cre.sub(replacement, message)

    return message
        
    
    
def init(instance):
    instance.registerUtil('localReplace', localReplace)
    

if "__main__" == __name__:
    print " revision 222", localReplace(" revision 222")
    print " wordthatendswithr 222", localReplace(" wordthatendswithr 222")
    print " r222", localReplace(" r222")
    print " r 222", localReplace(" r 222")
    print " #555", localReplace(" #555")
    
