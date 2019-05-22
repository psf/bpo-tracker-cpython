# OpenID Connect, using the oic library
# For Google accounts, also attempt migration from OpenID (until 2017)
import logging
import random
from UserDict import DictMixin
from oic.oic.consumer import Consumer
from oic.oic.message import RegistrationResponse
from oic.oic.message import AuthorizationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from roundup.cgi.actions import Action
from roundup.cgi.exceptions import *
from roundup import password, hyperdb

try:
    from oic.oauth2 import rndstr
except ImportError:
    import string

    def rndstr(size=16):
        """
        Returns a string of random ascii characters or digits
        :param size: The length of the string
        :return: string
        """
        _basech = string.ascii_letters + string.digits
        return "".join([random.choice(_basech) for _ in range(size)])

HOSTNAME='lap-le.pst.beuth-hochschule.de'

consumer_config = {
    'debug': True
}
client_config = {
    'client_authn_method':CLIENT_AUTHN_METHOD,
}
chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

PROVIDER_GOOGLE = 'Google'
PROVIDER_GITHUB = 'GitHub'
PROVIDER_URL_MAP = {
    PROVIDER_GOOGLE: 'https://accounts.google.com',
    PROVIDER_GITHUB: 'https://github.com/settings/developers',
}

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('bpo.extensions.oic_login')


def select_provider(form):
    if 'provider' in form:
        return form['provider'].value
    raise ValueError('Provider could not be found')


class SessionStore(DictMixin):
    def __init__(self, db):
        self.db = db

    def getitem(self, key):
        nodeid = self.db.oic_session.lookup(key)
        data = self.db.oic_session.get(nodeid, 'pickle')
        return cPickle.loads(data)

    def setitem(self, key, value):
        data = cPickle.dumps(value)
        try:
            nodeid = self.db.oic_session.lookup(key)
        except KeyError:
            self.db.oic_session.create(sid=key, pickle=data)
        else:
            self.db.oic_session.set(nodeid, pickle=data)
        self.db.commit()

    def delitem(self, key):
        nodeid = self.db.oic_session.lookup(key)
        self.db.oic_session.destroy(nodeid)

    def keys(self):
        res = []
        for nodeid in self.db.oic_session.nodeids():
            res.append(self.db.oic_session.get('sid'))
        return res

class OICMixin:
    def init_oic(self, provider_name):
        if provider_name not in PROVIDER_URL_MAP:
            raise ValueError('Invalid provider: %s', provider_name)
        provider = PROVIDER_URL_MAP[provider_name]
        logger.debug('Provider selected: %s', provider_name)
        self.scopes = ["openid", "profile", "email"]
        db = SessionStore(self.db)
        client = Consumer(db, consumer_config, client_config=client_config)
        client.allow['issuer_mismatch'] = True
        # GitHub does not support dynamically resolving OpenID configuration.
        if provider_name == PROVIDER_GITHUB:
            self.scopes = ["user:email", "read:user"]
            client.provider_info = {
                'authorization_endpoint': 'https://github.com/login/oauth/authorize',
                'token_endpoint': 'https://github.com/login/oauth/access_token'
            }
            client.handle_provider_config(client.provider_info, 'GitHub')
        else:
            client.provider_info = client.provider_config(provider)
        providers = self.db.oic_registration.filter(None, {'issuer': provider})
        assert len(providers) == 1
        provider = self.db.oic_registration.getnode(providers[0])
        client_reg = RegistrationResponse(client_id=provider['client_id'],
                                          client_secret=provider['client_secret'])
        client.store_registration_info(client_reg)
        logger.debug('Client preparation is completed.')
        return client

    def redirect_uri(self, provider):
        redirect_uri = '%sindex?@action=oic_authresp' % self.base
        # Avoid breaking existing google callback urls which will not have
        # provider tagged along
        if provider != PROVIDER_GOOGLE:
            redirect_uri += '&provider=%s' % provider
        return redirect_uri

class OICLogin(Action, OICMixin):
    def handle(self):
        provider = select_provider(self.client.form)
        client = self.init_oic(provider)
        redirect_uri = self.redirect_uri(provider)
        client.redirect_uris = [redirect_uri]

        client.state = rndstr()
        _nonce = rndstr()
        args = {
            #"client_id": client.client_id,
            "response_type": "code",
            "scope": self.scopes,
            "openid.realm": self.base+"?@action=openid_return",
            #"nonce": hmac.new(_nonce, digestmod=hashlib.sha224),
            "redirect_uri": client.redirect_uris[0]
            }
        result = client.do_authorization_request(state=client.state,
                                                 request_args=args)
        logger.debug('Result from authorization request: %d', result.status_code)
        if result.status_code == 302:
            location = result.headers['location']
            logger.debug('Redirecting to %s', location)
            raise Redirect(location)
        else:
            return "Could not contact Google" + repr(result.content)


class OICAuthResp(Action, OICMixin):
    def parse_authorization_response(self, client):
        return client.parse_response(AuthorizationResponse, info=self.client.env['QUERY_STRING'],
                                     sformat='urlencoded')

    def login(self, user):
        self.client.userid = user
        self.client.user = self.db.user.get(self.client.userid, 'username')
        # From LoginAction.verifyLogin
        if not self.hasPermission("Web Access"):
            raise LoginError(self._("You do not have permission to login"))
        # From LoginAction.handle
        self.client.opendb(self.client.user)
        self.client.session_api.set(user=self.client.user)
        if self.form.has_key('remember'):
            self.client.session_api.update(set_cookie=True, expire=24*3600*365)
        if self.form.has_key('__came_from'):
            raise Redirect(self.form['__came_from'].value)
        return

    def handle(self):
        provider = select_provider(self.client.form)
        client = self.init_oic(provider)
        redirect_uri = self.redirect_uri(provider)
        client.redirect_uris = [redirect_uri]

        aresp = self.parse_authorization_response(client)

        args = {
            "code": aresp["code"],
            "redirect_uri": client.redirect_uris[0],
            "client_id": client.client_id,
            "client_secret": client.client_secret
        }

        resp = client.do_access_token_request(scope=self.scopes,
                                              state=aresp["state"],
                                              request_args=args,
                                              authn_method="client_secret_post",
                                              headers={"Accept": "application/json"},
                                              )

        logger.debug('Access token request to %s provider was sent', provider)

        if provider == PROVIDER_GOOGLE:
            return self.on_google_response(client, resp)

        if provider == PROVIDER_GITHUB:
            return self.on_github_response(client, resp)

    def on_google_response(self, client, resp):
        try:
            id_token = resp['id_token']
        except KeyError:
            raise ValueError("Missing id_token from provider")
        else:
            iss = id_token['iss']
            if iss == 'accounts.google.com':
                iss = 'https://accounts.google.com'
            sub = id_token['sub']
            # find user by iss and sub
            oic_account = self.db.oic_account.filter(None, {'issuer':iss, 'subject':sub})
            if oic_account:
                # there should be only one user with that ID
                assert len(oic_account)==1
                user = self.db.oic_account.get(oic_account[0], 'user')
                return self.login(user)

            try:
                openid_id = id_token['openid_id']
                # find user by OpenID 2, then associate iss and sub
                user = self.db.user.filter(None, {'openids':openid_id})
                if user:
                    assert len(user)==1
                    user = user[0]
                    # store new oic credentials for this user
                    self.db.oic_account.create(user=user, issuer=iss, subject=sub)
                    # delete openid
                    openids = self.db.user.get(user, 'openids').split()
                    openids.remove(openid_id)
                    self.db.user.set(user, openids=' '.join(openids))
                    # commit and log in
                    self.db.commit()
                    return self.login(user)
            except KeyError:
                # no OpenID 2 migration
                pass

        # New user, request info from provider

        # XXX Google insists on GET
        aresp = self.parse_authorization_response(client)
        logger.debug('state: %s == %s', aresp["state"], resp["state"])
        userinfo = client.do_user_info_request(method="GET", state=aresp["state"])

        name = userinfo['name'].encode('utf-8')
        email = userinfo['email'].encode('utf-8')
        email_verified = userinfo['email_verified']

        # avoid creation of duplicate accounts
        users = self.db.user.filter(None, {'address': email})
        if users:
            raise ValueError("There is already an account for " + email)

        # Look for unused account name
        username = self.generate_username(name)

        # create account
        if email_verified:
            pw = password.Password(password.generatePassword())
            user = self.db.user.create(username=username,
                                       realname=name,
                                       password=pw,
                                       roles=self.db.config['NEW_WEB_USER_ROLES'],
                                       address=email)
            self.db.oic_account.create(user=user, issuer=iss, subject=sub)
            # complete login
            self.db.commit()
            return self.login(user)

        # email not verified: fail
        # In principle, it should be possible to do a email confirmation here
        # See previous versions of this file for an attempt to do so
        # However, the confrego action does not support preserving the OIC parameters,
        # as they live in a different table. This could be fixed by using an alternative
        # confirmation action. Doing so is deferred until need arises
        raise ValueError("Your OpenID Connect account is not supported. Please contact tracker-discuss@python.org")

    def on_github_response(self, client, response):
        if 'access_token' not in response:
            logger.debug('Invalid response from GitHub: %s', response)
            raise ValueError('Invalid response from GitHub')
        token = response['access_token']

        # Grab their info from the github api
        user_info = client.http_request(
            'https://api.github.com/user',
            method="GET",
            headers={
                'Authorization': 'token {}'.format(token),
                'User-Agent': 'bugs.python.org',
                'Accept': 'application/json',
            },
        )

        logger.debug('Trying to fetch user information from GitHub: %d', user_info.status_code)

        if user_info.status_code != 200:
            raise ValueError('Could not fetch user information')

        user_info = user_info.json()
        github_issuer = PROVIDER_URL_MAP[PROVIDER_GITHUB]
        github_id = str(user_info['id'])
        github_name = str(user_info['login'])
        github_email = str(user_info['email'])

        logger.debug('GitHub ID=%s, name=%s, email=%s', github_id, github_name, github_email)

        if user_info['email'] is not None:
            logger.debug('User ID %s does have a public email address', github_id)
            logger.debug('Checking BPO user with email address %s', github_email)

            # Try to combine with the existing user account first.
            users = self.db.user.filter(None, {'address': github_email})
            if users:
                if len(users) > 1:
                    raise ValueError(
                        'There are multiple accounts (%d) with your GitHub email address %s' % (len(users), github_email)
                    )
                logger.debug('BPO user with email address %s found: %s', github_email, users[0])
                # Check if user has previously authenticated with GitHub.
                oic_account = self.db.oic_account.filter(None, {'issuer': github_issuer, 'subject': github_id})
                if oic_account:
                    if len(oic_account) > 1:
                        raise ValueError('There are multiple records with the same issuer')
                    user = self.db.oic_account.get(oic_account[0], 'user')
                    logger.debug(
                        'BPO user with email address %s who has already been logged in with GitHub found: %s',
                        github_email, user,
                    )
                else:
                    user = users[0]
                    self.db.oic_account.create(user=user, issuer=github_issuer, subject=github_id)
                    self.db.commit()
                    logger.debug('BPO user ID %s with email address %s has linked to GitHub', user, github_email)
                logger.debug('Trying to log in to BPO with user ID %s and email address %s', user, github_email)
                return self.login(user)

        # Then check if user has already authenticated with GitHub.
        # TODO: Add user ID to filter
        oic_account = self.db.oic_account.filter(None, {'issuer': github_issuer, 'subject': github_id})
        if oic_account:
            logger.debug('Found existing linked account: %s (%s)', github_email, github_id)
            if len(oic_account) > 1:
                raise ValueError('There are multiple records with the same issuer')
            user = self.db.oic_account.get(oic_account[0], 'user')
            logger.debug('Fetched user ID %s from existing linked account: %s (%s)', user, github_email, github_id)
            return self.login(user)

        # Look for an unused account name.
        new_username = self.generate_username(github_name)
        pw = password.Password(password.generatePassword())
        user = self.db.user.create(
            username=new_username,
            realname=user_info['name'],
            github=user_info['login'],
            password=pw,
            roles=self.db.config['NEW_WEB_USER_ROLES'],
            address=github_email,
        )
        self.db.oic_account.create(user=user, issuer=github_issuer, subject=github_id)
        self.db.commit()
        logger.debug('New account with email %s and user ID %s has created', github_email, user)
        return self.login(user)

    def generate_username(self, username):
        new_username = username
        suffix = 1
        while True:
            user = self.db.user.filter(None, {'username': new_username})
            if not user:
                break
            suffix += 1
            new_username = '%s%d' % (username, suffix)
        logger.debug('Generated new username: %s', new_username)
        return new_username


class OICDelete(Action):
    def handle(self):
        if not self.form.has_key('openid'):
            self.client.add_error_message('OpenID required')
            return
        ID = self.form['openid'].value
        self.db.oic_account.retire(ID)
        self.db.commit()

def init(instance):
    instance.registerAction('oic_login', OICLogin)
    instance.registerAction('oic_authresp', OICAuthResp)
    instance.registerAction('oic_delete', OICDelete)
