import re

substitutions = [ (re.compile('\#(?P<ws>\s*)(?P<id>\d+)'),
                   "<a href='issue\g<id>'>#\g<ws>\g<id></a>" ),
                  ]

def localReplace(message):

    for cre, replacement in substitutions:
        message = cre.sub(replacement, message)

    return message
        
    
    
def init(instance):
    instance.registerUtil('localReplace', localReplace)
    
