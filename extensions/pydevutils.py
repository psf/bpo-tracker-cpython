import re
import json
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

def is_triager(request, userid):
    # We can't use 'request.client.userid' here because is_coordinator()
    # is used to determine if the current user is a coordinator. We need
    # 'userid' to determine if an arbitrary user is a triager.
    db = request.client.db
    query = db.user.get(userid, 'roles')
    # Disabled users have no roles so we need to check if 'userid' has
    # any roles.
    if query is None:
        return False
    return 'Developer' in query

def clean_ok_message(ok_message):
    """Remove nosy_count and message_count from the ok_message."""
    pattern = '\s*(?:nosy|message)_count,|,\s*(?:nosy|message)_count(?= edited)'
    return ''.join(re.sub(pattern, '', line) for line in ok_message) + '<br>'


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


def clas_as_json(request, cls):
    """
    Generate a JSON object that has the GitHub usernames as keys and as values
    true if the user signed the CLA, false if not, or none if there is no user
    associated with the GitHub username.
    """
    # pass the names as user?@template=clacheck&github_names=name1,name2
    names = request.form.getvalue('github_names')
    if names is None:
        # we got a request like user?@template=clacheck&github_names=
        return json.dumps({})  # return an empty JSON object

    names = names.split(',')
    user = request.client.db.user
    result = {}
    for name in names:
        # find all users with the given github name (case-insensitive)
        matches = user.stringFind(github=name)
        if matches:
            # if we have 1 (or more) user(s), see if at least one signed
            value = any(user.get(id, 'contrib_form') for id in matches)
        else:
            # otherwise the user has no associated bpo account
            value = None
        result[name] = value
    return json.dumps(result, separators=(',',':'))


class RandomIssueAction(Action):
    def handle(self):
        """Redirect to a random open issue."""
        issue = self.context['context']
        # use issue._klass to get a list of ids, and not a list of instances
        issue_ids = issue._klass.filter(None, {'status': '1'})
        if not issue_ids:
            raise Redirect(self.db.config.TRACKER_WEB)
        # we create our own Random instance so we don't have share the state
        # of the default Random instance. see issue 644 for details.
        rand = random.Random()
        url = self.db.config.TRACKER_WEB + 'issue' + rand.choice(issue_ids)
        raise Redirect(url)


class Redirect2GitHubAction(Action):
    def handle(self):
        """Redirect to the corresponding GitHub issue."""
        # pass the bpo id as issue?@action=redirect&bpo=ID
        issue = self.context['context']
        request = self.context['request']
        bpo_id = request.form.getvalue('bpo')
        if not bpo_id:
            return 'Please provide a bpo issue id with `&bpo=ID` in the URL.'
        try:
            bpo_id = int(bpo_id)
        except ValueError:
            return 'Please provide a valid bpo issue id.'
        try:
            gh_id = issue._klass.get(bpo_id, 'github')
        except IndexError:
            return 'There is no bpo issue with id {}.'.format(bpo_id)
        if not gh_id:
            return 'There is no GitHub id for bpo-{}.'.format(bpo_id)
        url = 'https://www.github.com/python/cpython/issues/{}'.format(gh_id)
        raise Redirect(url)


def openid_links(request):
    providers = [
        ('Google', 'oic_login', 'https://www.google.com/favicon.ico'),
        ('GitHub', 'oic_login', 'https://www.github.com/favicon.ico'),
        ('Launchpad', 'openid_login', 'https://launchpad.net/favicon.ico'),
    ]
    links = []
    for name, action, icon, in providers:
        links.append({
            'href': request.env['PATH_INFO'] + '?@action=' + action + '&provider=' + name,
            'src': icon,
            'title': name,
            'alt': name,
        })
    return links


def init(instance):
    instance.registerUtil('is_history_ok', is_history_ok)
    instance.registerUtil('is_coordinator', is_coordinator)
    instance.registerUtil('is_triager', is_triager)
    instance.registerUtil('clean_ok_message', clean_ok_message)
    instance.registerUtil('issueid_and_action_from_class',
                          issueid_and_action_from_class)
    instance.registerUtil('clas_as_json', clas_as_json)
    instance.registerAction('random', RandomIssueAction)
    instance.registerAction('redirect', Redirect2GitHubAction)
    instance.registerUtil('openid_links', openid_links)
