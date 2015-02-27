# OpenID Connect, using the oic library
# For Google accounts, also attempt migration from OpenID (until 2017)
from oic.oic.consumer import Consumer
from oic.oic.message import RegistrationResponse
from oic.oic.message import AuthorizationResponse
import hashlib
import hmac
from UserDict import DictMixin
from oic.oauth2 import rndstr
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from roundup.cgi.actions import Action
from roundup.cgi.exceptions import *
from roundup import password

HOSTNAME='lap-le.pst.beuth-hochschule.de'

consumer_config = {
    'debug': True
}
client_config = {
    'client_authn_method':CLIENT_AUTHN_METHOD,
}

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
    # XXX this somehow needs to be generalized if more OIC provider are supported
    provider = "https://accounts.google.com"
    def init_oic(self):
        self.scopes = ["openid","profile","email"]
        db = SessionStore(self.db)
        client = Consumer(db, consumer_config, client_config=client_config)
        client.allow['issuer_mismatch'] = True
        client.provider_info = client.provider_config(self.provider)
        providers = self.db.oic_registration.filter(None, {'issuer':self.provider})
        assert len(providers) == 1
        provider = self.db.oic_registration.getnode(providers[0])
        client_reg = RegistrationResponse(client_id=provider['client_id'],
                                          client_secret=provider['client_secret'])
        client.store_registration_info(client_reg)
        return client
    

class OICLogin(Action, OICMixin):
    def handle(self):
        client = self.init_oic()
        client.redirect_uris=[self.base+'index?@action=oic_authresp']

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
        if result.status_code == 302:
            raise Redirect, result.headers['location']
        else:
            return "Could not contact Google" + repr(result.content)


class OICAuthResp(Action, OICMixin):
    def login(self, user):
        self.client.userid = user
        self.client.user = self.db.user.get(self.client.userid, 'username')
        # From LoginAction.verifyLogin
        if not self.hasPermission("Web Access"):
            raise exceptions.LoginError, self._(
                "You do not have permission to login")
        # From LoginAction.handle
        self.client.opendb(self.client.user)
        self.client.session_api.set(user=self.client.user)
        if self.form.has_key('remember'):
            self.client.session_api.update(set_cookie=True, expire=24*3600*365)
        if self.form.has_key('__came_from'):
            raise Redirect, self.form['__came_from'].value
        return
        
    def handle(self):
        client = self.init_oic()
        client.redirect_uris=[self.base+'index?@action=oic_authresp']

        aresp = client.parse_response(AuthorizationResponse, info=self.client.env['QUERY_STRING'],
                                      sformat="urlencoded")

        code = aresp["code"]
        #assert aresp["state"] == client.state

        args = {
            "code": aresp["code"],
            "redirect_uri": client.redirect_uris[0],
            "client_id": client.client_id,
            "client_secret": client.client_secret
        }

        resp = client.do_access_token_request(scope=self.scopes,
                                              state=aresp["state"],
                                              request_args=args,
                                              authn_method="client_secret_post"
                                              )
        try:
            id_token = resp['id_token']
        except KeyError:
            raise ValueError, "Missing id_token from provider"
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
        userinfo = client.do_user_info_request(method="GET", state=aresp["state"])

        given_name = userinfo['given_name'].encode('utf-8')
        family_name = userinfo['family_name'].encode('utf-8')
        name = userinfo['name'].encode('utf-8')
        email = userinfo['email'].encode('utf-8')
        email_verified = userinfo['email_verified'] == 'true'

        # avoid creation of duplicate accounts
        users = self.db.user.filter(None, {'address': email})
        if users:
            raise ValueError, "There is already an account for " + email

        # create account
        pw = password.Password(password.generatePassword())
        user = self.db.user.create(username=name,
                                       realname=name,
                                       password=pw,
                                       roles=self.db.config['NEW_WEB_USER_ROLES'],
                                       address=email)
        self.db.oic_account.create(user=user, issuer=iss, subject=sub)
        if email_verified:
            # complete login
            self.db.commit()
            return self.login(user)

        # require email confirmation
        otks = self.db.getOTKManager()
        otk = ''.join([random.choice(chars) for x in range(32)])
        while otks.exists(otk):
            otk = ''.join([random.choice(chars) for x in range(32)])
        otks.set(otk, **user_props)

        # Send the email
        tracker_name = self.db.config.TRACKER_NAME
        tracker_email = self.db.config.TRACKER_EMAIL
        subject = 'Complete your registration to %s'%(tracker_name)
        body = """To complete your registration of the user "%(name)s" with
%(tracker)s, please visit the following URL:

%(url)s?@action=confrego&otk=%(otk)s

""" % {'name': name, 'tracker': tracker_name,
        'url': self.base, 'otk': otk}
        if not self.client.standard_message([user_props['address']], subject,
                body, (tracker_name, tracker_email)):
            return
        self.db.commit()

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
