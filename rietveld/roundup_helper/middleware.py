from models import Session, User
from codereview.models import Account
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.backends import RemoteUserBackend

class UserBackend(RemoteUserBackend):
    # auto-creation of django users should not be necessary,
    # as they should have been created before, so suppress it here.
    create_unknown_user = False

class LookupRoundupUser(object):

    def process_request(self, request):
        session_key = request.COOKIES.get(settings.TRACKER_COOKIE_NAME, None)
        if not session_key:
            self.logout(request)
            return
        session = Session.objects.filter(session_key = session_key)
        if not session:
            self.logout(request)
            return
        username = eval(session[0].session_value)['user']
        # the username comes from the cookie, so it really ought to exist
        roundup_user = User.objects.filter(_username=username)[0]
        # if we already have a user from the session, we are done.
        if request.user.is_authenticated():
            if request.user.username == username:
                return
        # We see the user for the first time. Authenticate it, and create
        # codereview account if none exists.
        user = auth.authenticate(remote_user=username)
        if not user:
            return
        # User is valid.  Set request.user and persist user in the session
        # by logging the user in.
        request.user = user
        account = Account.get_by_id(user.id)
        if not account:
            account = Account(id=user.id, user=user, email=user.email,
                              nickname=username, fresh=True)
            account.put()
        auth.login(request, user)
        
    def logout(self, request):
        # Clear django session if roundup session is gone.
        auth.logout(request)
