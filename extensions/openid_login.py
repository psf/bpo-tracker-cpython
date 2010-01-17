import openid, urllib, cgi, collections, calendar, time
from roundup.cgi.actions import Action, LoginAction, RegisterAction
from roundup.cgi.exceptions import *
from roundup import date, password

good_providers = ['Google', 'myOpenID', 'Launchpad']
providers = {}
for p in openid.providers:
    if p[0] not in good_providers: continue
    providers[p[0]] = p

class Openid:
    'Helper class for OpenID'

    # Session management: Recycle expired session objects
    def get_session(self, provider, discovered=None):
        sessions = self.db.openid_session.filter(None, {'provider_id':provider})
        for session_id in sessions:
            # Match may not have been exact
            if self.db.openid_session.get(session_id, 'provider_id') != provider:
                continue
            expires = self.db.openid_session.get(session_id, 'expires')
            if discovered and discovered[1] != self.db.openid_session.get(session_id, 'url'):
                # User has changed provider; don't reuse session
                break
            elif  expires > date.Date('.')+date.Interval("1:00"):
                # valid for another hour
                return self.db.openid_session.getnode(session_id)
            elif expires < date.Date('.')-date.Interval("1d"):
                # expired more than one day ago
                break
        else:
            session_id = None
        # need to create new session
        if discovered:
            stypes, url, op_local = discovered
        else:
            stypes, url, op_local = openid.discover(provider)
        now = date.Date('.')
        session_data = openid.associate(stypes, url)
        if session_id:
            session = self.db.openid_session.getnode(session_id)
            session.assoc_handle = session_data['assoc_handle']
        else:
            session_id = self.db.openid_session.create(assoc_handle=session_data['assoc_handle'])
            session = self.db.openid_session.getnode(session_id)
        session.provider_id = provider
        session.url = url
        session.stypes = " ".join(stypes)
        session.mac_key = session_data['mac_key']
        session.expires = now + date.Interval(int(session_data['expires_in']))
        self.db.commit()
        return session    
        
class OpenidLogin(LoginAction, Openid):
    'Extended versoin of LoginAction, supporting OpenID identifiers in username field.'
    def handle(self):
        if 'openid_identifier' in self.form:
            username = self.form['openid_identifier'].value
            # copy into __login_name for call to base action
            self.form.value.append(cgi.MiniFieldStorage('__login_name', username))
        else:
            # Let base action raise the exception
            return LoginAction.handle(self)
        if '__login_password' in self.form and self.form['__login_password'].value:
            # assume standard login if password provided
            return LoginAction.handle(self)
        try:
            self.db.user.lookup(username)
        except KeyError:
            # not a user name - it must be an openid
            pass
        else:
            return LoginAction.handle(self)
        # Login an OpenID
        type, claimed = openid.normalize_uri(username)
        if type == 'xri':
            raise ValueError, "XRIs are not supported"
        discovered = openid.discover(claimed)
        if not discovered:
            raise ValueError, "OpenID provider discovery failed"
        stypes, url, op_local = discovered
        session = self.get_session(claimed, discovered) # one session per claimed id
        realm = self.base+"?@action=openid_return"
        return_to = realm + "&__came_from=%s" % urllib.quote(self.client.path)
        url = openid.request_authentication(session.stypes, session.url,
                                            session.assoc_handle, return_to, realm=realm,
                                            claimed=claimed, op_local=op_local)
        raise Redirect, url
        

class OpenidProviderLogin(Action, Openid):
    'Login action with provider-guided login'
    def handle(self):
        if 'provider' not in self.form:
            self.client.error_message.append(self._('Provider name required'))
            return
        provider = self.form['provider'].value
        if provider not in providers:
            self.client.error_message.append(self._('Unsupported provider'))
            return
        provider_id = providers[provider][2]
        session = self.get_session(provider_id)
        realm = self.base+"?@action=openid_return"
        return_to = realm + "&__came_from=%s" % urllib.quote(self.client.path)
        url = openid.request_authentication(session.stypes, session.url,
                                            session.assoc_handle, return_to, realm=realm)
        raise Redirect, url

class OpenidReturn(Action):
    def handle(self):
        # parse again to get cgi kind of result
        query = cgi.parse_qs(self.client.env['QUERY_STRING'])
        if 'openid.identity' not in query:
            return self.rp_discovery()
        if 'openid.response_nonce' in query:
            nonce = query['openid.response_nonce'][0]
            stamp = openid.parse_nonce(nonce)
            utc = calendar.timegm(stamp.utctimetuple())
            if utc < time.time()-3600:
                # Old nonce
                raise ValueError, "Replay detected"
            try:
                self.db.openid_nonce.lookup(nonce)
            except KeyError:
                pass
            else:
                raise ValueError, "Replay detected"
            # Consume nonce; reuse expired nonces
            old = self.db.openid_nonce.filter(None, {'created':';.-1d'})
            stamp = date.Date(stamp)
            if old:
                self.db.openid_nonce.set(old[0], created=stamp, nonce=nonce)
            else:
                self.db.openid_nonce.create(created=stamp, nonce=nonce)
            self.db.commit()
        handle = query['openid.assoc_handle'][0]
        try:
            session = self.db.openid_session.lookup(handle)
        except KeyError:
            raise ValueError, 'Not authenticated (no session)'
        session = self.db.openid_session.getnode(session[0])
        try:
            signed = openid.authenticate(session, query)
        except Exception, e:
            raise ValueError, "Authentication failed: "+repr(e)
        if 'openid.claimed_id' in query:
            if 'claimed_id' not in signed:
                raise ValueError, 'Incomplete signature'
            claimed = query['openid.claimed_id'][0]
        else:
            # OpenID 1, claimed ID not reported - should set cookie
            if 'identity' not in signed:
                raise ValueError, 'Incomplete signature'
            claimed = query['openid.identity'][0]
        if self.user != 'anonymous':
            # Existing user claims OpenID

            # ID must be currently unassigned
            if self.db.user.filter(None, {'openids':claimed}):
                raise ValueError, 'OpenID already claimed'
            openids = self.db.user.get(self.userid, 'openids')
            if openids:
                openids += ' '
            else:
                openids = ''
            openids += claimed
            self.db.user.set(self.userid, openids=openids)
            self.db.commit()
            raise Redirect, '%suser%s' % (self.base, self.userid)

        # Check whether this is a successful login
        user = self.db.user.filter(None, {'openids':claimed})
        if user:
            # there should be only one user with that ID
            assert len(user)==1
            self.client.userid = user[0]
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

        # New user, bring up registration form
        self.client.classname = 'user'
        self.client.nodeid = None
        self.client.template = 'openid'
        openid_fields = []
        for key in self.form:
            if key.startswith('openid'):
                openid_fields.append((key, self.form.getfirst(key)))
        pt = self.client.instance.templates.get('user', 'openid')
        username = openid.get_username(query)
        realname = None
        if username:
            if isinstance(username, tuple):
                realname = ' '.join(username)
                username = '.'.join(username)
            username = username.replace(' ','.')
        result = pt.render(self.client, None, None,
                           realname=realname,
                           username=username,
                           email=openid.get_email(query),
                           claimed=claimed,
                           openid_fields=openid_fields)
        self.client.additional_headers['Content-Type'] = pt.content_type
        return result

class OpenidDelete(Action):
    def handle(self):
        if not self.form.has_key('openid'):
            self.client.error_message.append('OpenID required')
            return
        ID = self.form['openid'].value
        openids = self.db.user.get(self.userid, 'openids')
        if openids:
            openids = openids.split()
        else:
            openids = []
        if ID not in openids:
            raise ValueError, "You don't own this ID"
        openids.remove(ID)
        self.db.user.set(self.userid, openids=' '.join(openids))
        self.db.commit()

class OpenidRegister(RegisterAction):
    def handle(self):
        query = {}
        if 'openid.identity' not in self.form:
            raise ValueError, "OpenID fields missing"
        try:
            handle = self.form['openid.assoc_handle'].value
            session = self.db.openid_session.lookup(handle)
            session = self.db.openid_session.getnode(session[0])
        except Exception, e:
            raise ValueError, "Not authenticated (no session): "+str(e)
        # re-authenticate fields
        for key in self.form:
            if key.startswith("openid"):
                value = self.form[key].value
                try:
                    query[key].append(value)
                except KeyError:
                    query[key] = [value]
        try:
            signed = openid.authenticate(session, query)        
        except Exception, e:
            raise
            raise ValueError, "Authentication failed: "+repr(e)
        if 'openid.claimed_id' in query:
            if 'claimed_id' not in signed:
                raise ValueError, 'Incomplete signature'
            claimed = query['openid.claimed_id'][0]
        else:
            # OpenID 1, claimed ID not reported - should set cookie
            if 'identity' not in signed:
                raise ValueError, 'Incomplete signature'
            claimed = query['openid.identity'][0]

        # OpenID signature is still authentic, now pass it on to the base
        # register method; also fake password
        self.form.value.append(cgi.MiniFieldStorage('openids', claimed))
        pwd = password.generatePassword()
        self.form.value.append(cgi.MiniFieldStorage('password', pwd))
        self.form.value.append(cgi.MiniFieldStorage('@confirm@password', pwd))
        return RegisterAction.handle(self)

def openid_links(request):
    res = []
    for prov, icon, url in providers.values():
        res.append({'href':request.env['PATH_INFO']+'?@action=openid_login&provider='+prov,
                    'src':icon,
                    'title':prov})
    return res

def init(instance):
    instance.registerAction('login', OpenidLogin) # override standard login action
    instance.registerAction('openid_login', OpenidProviderLogin)
    instance.registerAction('openid_return', OpenidReturn)
    instance.registerAction('openid_delete', OpenidDelete)
    instance.registerAction('openid_register', OpenidRegister)
    instance.registerUtil('openid_links', openid_links)
