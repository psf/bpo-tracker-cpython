import openid2rp, urllib, cgi, collections, calendar, time
from roundup.cgi.actions import Action, LoginAction, RegisterAction
from roundup.cgi.exceptions import *
from roundup import date, password

providers = {}
for p in (
    ('Google', 'https://www.google.com/favicon.ico', 'https://www.google.com/accounts/o8/id'),
    ('Launchpad', 'https://launchpad.net/favicon.ico', 'https://login.launchpad.net/')
    ):
    providers[p[0]] = p

class Openid:
    'Helper class for OpenID'

    # Session management: Recycle expired session objects
    def get_session(self, url, stypes):
        sessions = self.db.openid_session.filter(None, {'url':url})
        for session_id in sessions:
            # Match may not have been exact
            if self.db.openid_session.get(session_id, 'url') != url:
                continue
            expires = self.db.openid_session.get(session_id, 'expires')
            if  expires > date.Date('.')+date.Interval("1:00"):
                # valid for another hour
                return self.db.openid_session.getnode(session_id)
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
        session.url = url
        session.mac_key = session_data['mac_key']
        session.expires = now + date.Interval(int(session_data['expires_in']))
        self.db.commit()
        return session

    def discover(self, url):
        '''Return cached discovery results or None.'''
        try:
            discovered = self.db.openid_discovery.lookup(url)
        except KeyError:
            return None
        discovered = self.db.openid_discovery.getnode(discovered)
        op_local = discovered.op_local
        if op_local == '':
            op_local = None
        return discovered.services.split(), discovered.op_endpoint, op_local

    def store_discovered(self, url, stypes, op_endpoint, op_local):
        if op_local is None:
            op_local = ''
        try:
            discovered = self.db.openid_discovery.lookup(url)
        except KeyError:
            self.db.openid_discovery.create(url=url, services=" ".join(stypes),
                                            op_endpoint=op_endpoint, op_local=op_local)
        else:
            discovered = self.db.openid_discovery.getnode(discovered)
            discovered.services = " ".join(stypes)
            discovered.op_endpoint = op_endpoint
            discovered.op_local = op_local
            self.db.commit()

    def find_association(self, handle):
        try:
            session = self.db.openid_session.lookup(handle)
            session = self.db.openid_session.getnode(session)
            return session
        except KeyError:
            return None

    def nonce_seen(self, nonce):
        try:
            self.db.openid_nonce.lookup(nonce)
            return True
        except KeyError:
            return False

    def authenticate(self, query):
        '''Authenticate an OpenID indirect response, and return the claimed ID'''
        try:
            signed, claimed = openid2rp.verify(query, self.discover,
                                               self.find_association,
                                               self.nonce_seen)
        except Exception, e:
            raise ValueError, "Authentication failed: "+str(e)
        return claimed

    def store_nonce(self, query):
        '''Store a nonce in the database.'''
        if 'openid.response_nonce' in query:
            nonce = query['openid.response_nonce'][0]
            stamp = openid2rp.parse_nonce(nonce)
            # Consume nonce; reuse expired nonces
            old = self.db.openid_nonce.filter(None, {'created':';.-1d'})
            stamp = date.Date(stamp)
            if old:
                self.db.openid_nonce.set(old[0], created=stamp, nonce=nonce)
            else:
                self.db.openid_nonce.create(created=stamp, nonce=nonce)
            self.db.commit()
        
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
        self.store_discovered(claimed, *discovered)
        stypes, url, op_local = discovered
        session = self.get_session(url, stypes)
        realm = self.base+"?@action=openid_return"
        return_to = realm + "&__came_from=%s" % urllib.quote(self.client.path)
        url = openid2rp.request_authentication(stypes, url,
                                            session.assoc_handle, return_to, realm=realm,
                                            claimed=claimed, op_local=op_local)
        raise Redirect, url
        

class OpenidProviderLogin(Action, Openid):
    'Login action with provider-guided login'
    def handle(self):
        if 'provider' not in self.form:
            self.client.add_error_message(self._('Provider name required'))
            return
        provider = self.form['provider'].value
        if provider not in providers:
            self.client.add_error_message(self._('Unsupported provider'))
            return
        provider_id = providers[provider][2]
        # For most providers, it would be reasonable to cache the discovery
        # results. However, the risk of login breaking if a provider does change
        # its service URL outweighs the cost of another HTTP request to perform
        # the discovery during login.
        try:
            result = openid2rp.discover(provider_id)
        except Exception:
            result = None
        if result is None:
            self.client.add_error_message('Provider %s appears to be down' % providers[provider][0])
            return
        services, op_endpoint, op_local = result
        session = self.get_session(op_endpoint, services)
        realm = self.base+"?@action=openid_return"
        return_to = realm + "&__came_from=%s" % urllib.quote(self.client.path)
        url = openid2rp.request_authentication(services, op_endpoint,
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
        handle = query['openid.assoc_handle'][0]
        try:
            session = self.db.openid_session.lookup(handle)
        except KeyError:
            raise ValueError, 'Not authenticated (no session)'
        session = self.db.openid_session.getnode(session)
        claimed = self.authenticate(query)
        if self.user != 'anonymous':
            # Existing user claims OpenID

            # ID must be currently unassigned
            if self.db.user.filter(None, {'openids':claimed}):
                raise ValueError, 'OpenID already claimed'
            # Consume nonce
            self.store_nonce(query)
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
            # Consume nonce
            self.store_nonce(query)
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
        pt = self.client.instance.templates.load('user.openid')
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
            self.client.add_error_message('OpenID required')
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
        # re-authenticate fields
        for key in self.form:
            if key.startswith("openid"):
                value = self.form[key].value
                try:
                    query[key].append(value)
                except KeyError:
                    query[key] = [value]
        claimed = self.authenticate(query)
        # OpenID signature is still authentic, now pass it on to the base
        # register method; also fake password

        # Consume nonce first
        self.store_nonce(query)
        
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
                    'title':prov,
                    'alt':prov})
    return res

def init(instance):
    instance.registerAction('login', OpenidLogin) # override standard login action
    instance.registerAction('openid_login', OpenidProviderLogin)
    instance.registerAction('openid_return', OpenidReturn)
    instance.registerAction('openid_delete', OpenidDelete)
    instance.registerAction('openid_register', OpenidRegister)
    instance.registerUtil('openid_links', openid_links)
