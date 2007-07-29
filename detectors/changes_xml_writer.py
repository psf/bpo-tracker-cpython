#
#  changes.xml writer detector.
#
# Copyright (c) 2007  Michal Kwiatkowski <constant.beta@gmail.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# * Neither the name of the author nor the names of his contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""changes.xml writer detector -- save each database change to an XML file.

Root element is called `changes` and it has at most `ChangesXml.max_items`
children, each called a `change`. Each `change` has the following attributes:

:date:  date in RFC2822 format when the change was made
:id:    unique identifier of this change (note: not an integer)
:type:  type of this change (see below)

A structure of a `change` depends on its `type`. Currently implemented
change types and their formats are listed below.

* type = `file-added`

  Describes a new file attached to an existing issue. Child elements:

  :file-id:   unique integer identifier of the file
  :file-name: name of the uploaded file
  :file-type: MIME type of the file content
  :file-url:  permanent URL of the file
  :issue-id:  unique integer identifier of an issue this file is attached to
"""

import os
import urllib
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from time import gmtime, strftime

# Relative to tracker home directory.
FILENAME = os.path.join('%(TEMPLATES)s', 'recent-changes.xml')


def tracker_url(db):
    return str(db.config.options[('tracker', 'web')])

def changes_xml_path(db):
    return os.path.join(db.config.HOME, FILENAME % db.config.options)

def rfc2822_date():
    return strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

class File(object):
    def __init__(self, db, id, issue_id):
        self.db = db
        self.id = id
        self.issue_id = issue_id

        self.name = db.file.get(id, 'name')
        self.type = db.file.get(id, 'type')
        # Based on roundup.cgi.templating._HTMLItem.download_url().
        self.download_url = tracker_url(self.db) +\
            urllib.quote('%s%s/%s' % ('file', self.id, self.name))

class ChangesXml(object):
    # Maximum number of changes stored in a file.
    max_items = 20

    def __init__(self, filename):
        self.filename = filename
        self._read_document()
        self.modified = False

    def save(self):
        if not self.modified:
            return

        self._trim_to_max_items()

        fd = open(self.filename, 'w')
        self.document.writexml(fd, encoding="UTF-8")
        fd.close()

    def add_file(self, file):
        change = self._change("file%s-added-to-issue%s" % (file.id, file.issue_id),
                              "file-added")

        change.appendChild(self._element_with_text("file-id",   file.id))
        change.appendChild(self._element_with_text("file-name", file.name))
        change.appendChild(self._element_with_text("file-type", file.type))
        change.appendChild(self._element_with_text("file-url",  file.download_url))
        change.appendChild(self._element_with_text("issue-id",  file.issue_id))

        self.root.appendChild(change)
        self.modified = True

    def add_files(self, files):
        for file in files:
            self.add_file(file)

    def _change(self, id, type):
        """Return new 'change' element of a given type.
           <change id='id' date='now' type='type'></change>
        """
        change = self.document.createElement("change")
        change.setAttribute("id",   id)
        change.setAttribute("type", type)
        change.setAttribute("date", rfc2822_date())
        return change

    def _element_with_text(self, name, value):
        """Return new element with given name and text node as a value.
           <name>value</name>
        """
        element = self.document.createElement(name)
        text = self.document.createTextNode(str(value))
        element.appendChild(text)
        return element

    def _trim_to_max_items(self):
        """Remove changes exceeding self.max_items.
        """
        # Assumes that changes are stored sequentially from oldest to newest.
        # Will do for now.
        for change in self.root.getElementsByTagName("change")[0:-self.max_items]:
            self.root.removeChild(change)

    def _read_document(self):
        try:
            self.document = minidom.parse(self.filename)
            self.root = self.document.firstChild
        except IOError, e:
            # File not found, create a new one then.
            if e.errno != 2:
                raise
            self._create_new_document()
        except ExpatError:
            # File has been damaged, forget about it and create a new one.
            self._create_new_document()

    def _create_new_document(self):
        self.document = minidom.Document()
        self.root = self.document.createElement("changes")
        self.document.appendChild(self.root)

def get_new_files_ids(issue_now, issue_then):
    """Return ids of files added between `now` and `then`.
    """
    files_now = set(issue_now['files'])
    if issue_then:
        files_then = set(issue_then['files'])
    else:
        files_then = set()
    return map(int, files_now - files_then)

def file_added_to_issue(db, cl, issue_id, olddata):
    try:
        changes   = ChangesXml(changes_xml_path(db))
        issue     = db.issue.getnode(issue_id)
        new_files = [ File(db, id, issue_id) for id in get_new_files_ids(issue, olddata) ]

        changes.add_files(new_files)
        changes.save()
    except:
        # We can't mess up with a database commit.
        pass


def init(db):
    db.issue.react('create', file_added_to_issue)
    db.issue.react('set',    file_added_to_issue)
