"""
cas_client.py

A convenient wrapper around the central authentication system.

@authors: Scott Karlin, Alex Halderman, Brian Kernighan, Bob Dondero

@modified: Ported to Python 3.7 & Flask by Chege Gitau

"""

import urllib
import re

#-----------------------------------------------------------------------

class CASClient:
    """
    A convenient wrapper around the central authentication system.

    """
    #-------------------------------------------------------------------
    
    def __init__(self, url='https://fed.princeton.edu/cas/'):
        """
        Initialize a new CASClient object so it uses the given CAS server

        :param url: ``str`` 
        
        The URL of the CAS server. Defaults to ``fed.princeton.edu`` if no 
        server URL is given.

        """
        self.cas_url = url

    #-------------------------------------------------------------------
	
    def strip_ticket(self, request):
        """
        :param request: ``flask.Request``

        A request that occurs as part of the CAS authentication process.

        :return: ``str``
        
        The URL of the current request after stripping out the `ticket` 
        parameter added by the CAS server.
        
        """
        url = request.url
        if url is None: return "something is badly wrong"
        url = re.sub(r'ticket=[^&]*&?', '', url)
        url = re.sub(r'\?&?$|&$', '', url)
        return url
        
    #-------------------------------------------------------------------

    def validate(self, ticket, request):
        """
        Validate a login ticket by contacting the CAS server.

        :param request: ``str``

        A ticket that can be validated by CAS. Once a user authenticates 
        themselves with CAS, CAS makes a GET request to the application. This 
        GET request contains a ticket as one of its parameters.

        :param request: ``flask.Request``

        A request that occurs as part of the CAS authentication process.

        :return: ``str``

        The user's username if valid

        :return: ``NoneType``
        
        Returned if the user is invalid
        """
        val_url = self.cas_url + "validate" + \
            '?service=' + urllib.request.quote(self.strip_ticket(request)) + \
            '&ticket=' + urllib.request.quote(ticket)
        r = urllib.request.urlopen(val_url).readlines()   # returns 2 lines
        r = [byte_string.decode("utf-8") for byte_string in r]
        if len(r) == 2 and re.match("yes", r[0]) is not None:
            return r[1].strip()
        return None
        
    #-------------------------------------------------------------------
   	
    def authenticate(self, request, redirect, session):
        """
        Authenticate the remote user.

        :param request: ``flask.Request``

        A request that occurs as part of the CAS authentication process.

        :param redirect: ``flask.redirect``

        A function that, if called, returns a 3xx response

        :param session: ``flask.session``

        A session object whose values can be accessed by the rest of the 
        application. If the authentication is successful, the ``username`` 
        attribute will be set.

        :return: ``str``

        If the user has been successfully authenticated, return their username

        :return: ``flask.Response(code=302)``

        If the user has not been successfully authenticated, redirect them to 
        the CAS server's login page.

        """
        
        # If the user's username is in the session, then the user was
        # authenticated previously.  So return the user's username.
        username = session.get('username')
        if username is not None: return username
           
        # If the request contains a login ticket, then try to validate it.
        ticket = request.args.get('ticket')
        if ticket is not None:
            username = self.validate(ticket, request)
            if username is not None:             
                # The user is authenticated, so store the user's
                # username in the session.               
                session['username'] = username        
                return username
      
        # The request does not contain a valid login ticket, so
        # redirect the browser to the login page to get one.
        login_url = self.cas_url + 'login' \
            + '?service=' + urllib.request.quote(self.strip_ticket(request))
            
        return redirect(login_url)

#-----------------------------------------------------------------------
