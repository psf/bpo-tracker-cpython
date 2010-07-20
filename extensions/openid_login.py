import openid2rp, urllib, cgi, collections, calendar, time
from roundup.cgi.actions import Action, LoginAction, RegisterAction
from roundup.cgi.exceptions import *
from roundup import date, password

providers = {}
for p in (
    ('Google', 'http://www.google.com/favicon.ico', 'https://www.google.com/accounts/o8/id'),
    ('myOpenID', 'https://www.myopenid.com/favicon.ico', 'https://www.myopenid.com/'),
    ('Launchpad', 'https://login.launchpad.net/favicon.ico', 'https://login.launchpad.net/')
    ):
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
            if discovered and discovered[1] != self.db.openid_session.get(session_id, 'url'):
                # User has changed provider; don't reuse session
                continue
            expires = self.db.openid_session.get(session_id, 'expires')
            if  expires > date.Date('.')+date.Interval("1:00"):
                # valid for another hour
                return self.db.openid_session.getnode(session_id)
        # need to create new session, or recycle an expired one
        if discovered:
            stypes, url, op_local = discovered
        else:
            stypes, url, op_local = openid2rp.discover(provider)
        now = date.Date('.')
        session_data = openid2rp.associate(stypes, url)
        # check whether a session has expired a day ago
        sessions = self.db.openid_session.filter(None, {'expires':'to -1d'})
        if sessions:
            session = self.db.openid_session.getnode(sessions[0])
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

    def authenticate(self, session, query):
        '''Authenticate an OpenID indirect response, and return the claimed ID'''
        try:
            signed = openid2rp.authenticate(session, query)
        except Exception, e:
            raise ValueError, "Authentication failed: "+str(e)
        if openid2rp.is_op_endpoint(session.stypes):
            # Provider-guided login: provider ought to report claimed ID
            if 'openid.claimed_id' in query:
                claimed = query['openid.claimed_id'][0]
            else:
                raise ValueError, 'incomplete response'
            # OpenID 11.2: verify that provider is authorized to assert ID
            discovered = openid2rp.discover(claimed)
            if not discovered or discovered[1] != session.url:
                raise ValueError, "Provider %s is not authorized to make assertions about %s" % (session.url, claimed)
        else:
            # User entered claimed ID, stored in session object
            claimed = session.provider_id
            if not openid2rp.is_compat_1x(session.stypes):
                # can only check correct claimed ID for OpenID 2.0
                if 'openid.claimed_id' not in query or claimed != query['openid.claimed_id'][0]:
                    # assertion is not about an ID, or about a different ID; refuse to accept
                    raise ValueError, "Provider did not assert your ID"
        return claimed

        
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
        type, claimed = openid2rp.normalize_uri(username)
        if type == 'xri':
            raise ValueError, "XRIs are not supported"
        discovered = openid2rp.discover(claimed)
        if not discovered:
            raise ValueError, "OpenID provider discovery failed"
        stypes, url, op_local = discovered
        session = self.get_session(claimed, discovered) # one session per claimed id
        realm = self.base+"?@action=openid_return"
        return_to = realm + "&__came_from=%s" % urllib.quote(self.client.path)
        url = openid2rp.request_authentication(session.stypes, session.url,
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
        url = openid2rp.request_authentication(session.stypes, session.url,
                                            session.assoc_handle, return_to, realm=realm)
        raise Redirect, url

class OpenidReturn(Action, Openid):
    def handle(self):
        # parse again to get cgi kind of result
        query = cgi.parse_qs(self.client.env['QUERY_STRING'])
        if 'openid.identity' not in query:
            # RP discovery
            payload = '''<xrds:XRDS xmlns:xrds="xri://$xrds"  
                                    xmlns="xri://$xrd*($v*2.0)">  
                <XRD>  
                     <Service priority="1">  
                              <Type>http://specs.openid.net/auth/2.0/return_to</Type>  
                              <URI>%s?@action=openid_return</URI>  
                     </Service>  
                </XRD>  
                </xrds:XRDS>
            ''' % self.base
            self.client.additional_headers['Content-Type'] = 'application/xrds+xml'
            return payload
        if 'openid.response_nonce' in query:
            nonce = query['openid.response_nonce'][0]
            stamp = openid2rp.parse_nonce(nonce)
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
        session = self.db.openid_session.getnode(session)
        claimed = self.authenticate(session, query)
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
        username = openid2rp.get_username(query)
        realname = None
        if username:
            if isinstance(username, tuple):
                realname = ' '.join(username)
                username = '.'.join(username)
            username = username.replace(' ','.')
        result = pt.render(self.client, None, None,
                           realname=realname,
                           username=username,
                           email=openid2rp.get_email(query),
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

class OpenidRegister(RegisterAction, Openid):
    def handle(self):
        query = {}
        if 'openid.identity' not in self.form:
            raise ValueError, "OpenID fields missing"
        try:
            handle = self.form['openid.assoc_handle'].value
            session = self.db.openid_session.lookup(handle)
            session = self.db.openid_session.getnode(session)
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
        claimed = self.authenticate(session, query)
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
