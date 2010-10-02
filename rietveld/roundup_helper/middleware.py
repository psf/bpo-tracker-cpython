from models import Session, User
from django.contrib import auth
from django.contrib.auth.backends import RemoteUserBackend

class UserBackend(RemoteUserBackend):
    def configure_user(self, user):
        roundup_user = User.objects.filter(_username=user.username)[0]
        user.email = roundup_user._address
        user.save()
        from codereview import models
        account = models.Account.get_account_for_user(user)
        account.nickname = user.username
        account.save()
        return user

class LookupRoundupUser(object):

    def process_request(self, request):
        session_key = request.COOKIES.get('roundup_session_Tracker', None)
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
        if not roundup_user._address:
            # Rietveld insists that user objects must have email addresses
            return
        # Taken from RemoteUserMiddleware: auto-create the user if it's new
        if request.user.is_authenticated():
            if request.user.username == username:
                return
        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(remote_user=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)
        
    def logout(self, request):
        # Clear django session if roundup session is gone.
        auth.logout(request)
