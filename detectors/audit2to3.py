import roundup
import roundup.instance
import sets

def update2to3(db, cl, nodeid, newvalues):
    '''Component 2to3 issues to be assigned to collinwinter unless otherwise
       assigned.
    '''
    # nodeid will be None if this is a new node
    componentIDS=None
    if nodeid is not None:
        componentIDS = cl.get(nodeid, 'components')
    if newvalues.has_key('components'):
        componentIDS = newvalues['components']
    if componentIDS and (theComponent in componentIDS):
        if not newvalues.has_key('assignee') or \
               newvalues['assignee'] == Nobody:
            newvalues['assignee'] = theMan

def init(db):
    global theMan, theComponent, Nobody
    theMan = db.user.lookup('collinwinter')
    Nobody = db.user.lookup('nobody')
    theComponent = db.component.lookup('2to3 (2.x to 3.0 conversion tool)')

    db.issue.audit('create', update2to3)
    db.issue.audit('set', update2to3)

if __name__ == '__main__':
    global theMan, theComponent, Nobody
    instanceHome='/home/roundup/trackers/tracker'
    instance = roundup.instance.open(instanceHome)
    db = instance.open('admin')
    cl = db.issue
    nodeID = '1002'
    theMan = db.user.lookup('collinwinter')
    Nobody = db.user.lookup('nobody')
    theComponent = db.component.lookup('2to3 (2.x to 3.0 conversion tool)')
    newvalues = { 'components': [theComponent] , 'assignee': Nobody}
    update2to3(db, cl, nodeID, newvalues)
    print Nobody, theMan, theComponent, newvalues
