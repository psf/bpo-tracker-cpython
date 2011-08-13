"""
This module provides two helper functions used by the Javascript autocomplete
of the nosy list:
  1) a simple state machine to parse the tables of the
     experts index and turn them in a JSON object;
  2) a function to get the list of developers as a JSON object;
"""

import urllib
try:
    import json
except ImportError:
    import simplejson as json

url = 'http://hg.python.org/devguide/raw-file/default/experts.rst'

# possible states
no_table = 0  # not parsing a table
table_header = 1  # parsing the header
table_content = 2  # parsing the content
table_end = 3  # reached the end of the table

def experts_as_json():
    """
    Parse the tables of the experts index and turn them into a JSON object.
    """
    data = {}
    table_state = no_table

    try:
        page = urllib.urlopen(url)
    except Exception:
        # if something goes wrong just return an empty JSON object
        return '{}'

    for line in page:
        columns = [column.strip() for column in line.split('  ', 1)]
        # all the tables have 2 columns (some entries might not have experts,
        # so we just skip them)
        if len(columns) != 2:
            continue
        first, second = columns
        # check if we found a table separator
        if set(first) == set(second) == set('='):
            table_state += 1
            if table_state == table_end:
                table_state = no_table
            continue
        if table_state == table_header:
            # create a dict for the category (e.g. 'Modules', 'Interest areas')
            category = first
            data[category] = {}
        if table_state == table_content:
            # add to the category dict the entries for that category
            # (e.g.module names) and the list of experts
            # if the entry is empty the names belong to the previous entry
            entry = first or entry
            names = (name.strip(' *') for name in second.split(','))
            names = ','.join(name for name in names if '(inactive)' not in name)
            if not first:
                data[category][entry] += names
            else:
                data[category][entry] = names
    return json.dumps(data, separators=(',',':'))


def devs_as_json(cls):
    """
    Generate a JSON object that contains the username and realname of all
    the committers.
    """
    users = []
    for user in cls.filter(None, {'iscommitter': 1}):
        username = user.username.plain()
        realname = user.realname.plain(unchecked=1)
        if not realname:
            continue
        users.append([username, realname])
    return json.dumps(users, separators=(',',':'))


def init(instance):
    instance.registerUtil('experts_as_json', experts_as_json)
    instance.registerUtil('devs_as_json', devs_as_json)
