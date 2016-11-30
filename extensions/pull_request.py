
baseurl = 'https://github.com/python/cpython/pull/'

def get_pr_url(pr):
    """Transforms pr into a working URL."""
    return '<a href="%s%s" title="%s">PR %s</a>' % (baseurl, pr.number, pr.title, pr.number)


def init(instance):
    instance.registerUtil('get_pr_url', get_pr_url)

