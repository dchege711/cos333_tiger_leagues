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
    Initialize a new CASClient object so it uses the given CAS server, or 
    `fed.princeton.edu` if no server is given.
    """

    #-------------------------------------------------------------------
    
    def __init__(self, url='https://fed.princeton.edu/cas/'):
        self.cas_url = url

    #-------------------------------------------------------------------
	
    def strip_ticket(self, request):
        """
        @return `str`: the URL of the current request after stripping out the 
        `ticket` parameter added by the CAS server.
        """
        url = request.url
        if url is None:
            return "something is badly wrong"
        url = re.sub(r'ticket=[^&]*&?', '', url)
        url = re.sub(r'\?&?$|&$', '', url)
        return url
        
    #-------------------------------------------------------------------

    def validate(self, ticket, request):
        """
        Validate a login ticket by contacting the CAS server.

        @return `str` the user's username if valid
        @return `None` if the user is invalid
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
        Authenticate the remote user, and return the user's username.
        Do not return unless the user is successfully authenticated.

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
