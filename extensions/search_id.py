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
        if len(split) > 50:
            # Postgres crashes on log queries
            raise exceptions.FormError("too many search terms")

def init(instance):
    instance.registerAction('searchid', SearchIDAction)
