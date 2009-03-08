from roundup.cgi.actions import Action
from roundup.cgi import exceptions

class SearchIDAction(Action):
    def handle(self):
        request = self.context['request']
        split = request.search_text.split()
        if len(split) == 1:
            id = split[0]
            if id.isdigit():
                if self.db.hasnode('issue', id):
                    raise exceptions.Redirect('issue'+id)

def init(instance):
    instance.registerAction('searchid', SearchIDAction)
