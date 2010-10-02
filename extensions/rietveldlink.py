def rietveldlink(request, issueid, fileid):
    if request.client.db.file.get(fileid, 'patchset'):
        return '/review/%s/show' % issueid
    return ""

def init(instance):
    instance.registerUtil('rietveldlink', rietveldlink)
