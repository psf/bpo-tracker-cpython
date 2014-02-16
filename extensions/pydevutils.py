import re
import random
from roundup.cgi.actions import Action
from roundup.cgi.exceptions import Redirect


def is_history_ok(request):
    user = request.client.userid
    db = request.client.db
    classname = request.classname
    nodeid = request.nodeid
    # restrict display of user history to user itself only
    if classname == 'user':
        return user == nodeid or 'Coordinator' in db.user.get(user, 'roles')
    # currently not used
    return True

def is_coordinator(request):
    user = request.client.userid
    db = request.client.db
    return 'Coordinator' in db.user.get(user, 'roles')

def clean_ok_message(ok_message):
    """Remove nosy_count and message_count from the ok_message."""
    pattern = '\s*(?:nosy|message)_count,|,\s*(?:nosy|message)_count(?= edited)'
    return '\n'.join(re.sub(pattern, '', line) for line in ok_message) + '\n'


def issueid_and_action_from_class(cls):
    """
    Return the id of the issue where the msg/file is/was linked
    and if the last "linking action" was 'link' or 'unlink'.
    """
    last_action = ''
    for entry in cls._klass.history(cls._nodeid):
        if 'unlink' in entry:
            last_unlink = entry
            last_action = 'unlink'
        elif 'link' in entry:
            last_entry = entry
            last_action = 'link'
    if last_action in ('link', 'unlink'):
        # the msg has been unlinked and not linked back
        # the link looks like: ('16', <Date 2011-07-22.05:14:12.342>, '4',
        #                       'link', ('issue', '1', 'messages'))
        return last_entry[4][1], last_action
    return None, None


class RandomIssueAction(Action):
    def handle(self):
        """Redirect to a random open issue."""
        issue = self.context['context']
        # use issue._klass to get a list of ids, and not a list of instances
        issue_ids = issue._klass.filter(None, {'status': 1})
        url = self.db.config.TRACKER_WEB + 'issue' + random.choice(issue_ids)
        raise Redirect(url)


def init(instance):
    instance.registerUtil('is_history_ok', is_history_ok)
    instance.registerUtil('is_coordinator', is_coordinator)
    instance.registerUtil('clean_ok_message', clean_ok_message)
    instance.registerUtil('issueid_and_action_from_class',
                          issueid_and_action_from_class)
    instance.registerAction('random', RandomIssueAction)
