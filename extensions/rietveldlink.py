def rietveldlink(request, issueid, fileid):
    patchset = request.client.db.file.get(fileid, 'patchset'):
    if patchset and patchset != 'n/a':
        return '/review/%s/show' % issueid
    return ""

def init(instance):
    instance.registerUtil('rietveldlink', rietveldlink)
