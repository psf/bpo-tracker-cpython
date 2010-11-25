import cgi
from roundup.cgi.actions import Action
from roundup.cgi import exceptions

class SearchIDAction(Action):
    def handle(self):
        request = self.context['request']
        if not request.search_text:
            raise exceptions.FormError("Missing search text")
        split = request.search_text.split()
        if len(split) == 1:
            id = split[0]
            if id.isdigit():
                if self.db.hasnode('issue', id):
                    raise exceptions.Redirect('issue'+id)
        if len(split) > 50:
            # Postgres crashes on long queries
            raise exceptions.FormError("too many search terms")

class OpenSearchAction(SearchIDAction):
    """Action referred to in the Open Search Description.
    This has just a single query parameter (in addition to the action
    name), and fills out the rest here.
    """
    def handle(self):
        # Check for IDs first
        SearchIDAction.handle(self)
        # regular search, fill out query parameters
        for k, v in [('@columns', 'id,activity,title,creator,assignee,status,type'), #columns_showall
                     ('@sort', '-activity'),
                     ('ignore', 'file:content')]:
            self.form.value.append(cgi.MiniFieldStorage(k, v))


def init(instance):
    instance.registerAction('searchid', SearchIDAction)
    instance.registerAction('opensearch', OpenSearchAction)
