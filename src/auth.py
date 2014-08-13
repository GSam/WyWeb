# -*- encoding: UTF-8 -*-
#
# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#

import cherrypy
import db 

import uuid
import hashlib

from mako.template import Template
from mako.lookup import TemplateLookup
import config

lookup = TemplateLookup(directories=['html'])

SESSION_KEY = '_cp_username'
 
#def hash_password(password):
    # uuid is used to generate a random number
#    salt = uuid.uuid4().hex
#    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
#def check_password(hashed_password, user_password):
#    password, salt = hashed_password.split(':')
#    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()
 

#TO HASH PASSWORD hashed_password = hash_password(new_pass) 
#check_password(hashed_password, old_pass)


def check_credentials(user, passwd):
    """Verifies credentials for username and password.
    Returns None on success or a string describing the error on failure"""

    cnx = db.connect()[0]
    if cnx:
        cursor = cnx.cursor()
        query = ("SELECT * from whiley_user where username = '" + user + "' and password = '" + passwd + "'")
        #query = ("SELECT * from whiley_user")
        cursor.execute(query)
        row = cursor.fetchone()
        if cursor.rowcount > 0:
            #print("{} passwd".format(row[2]))
            #hashed_password = hash_password(passwd)
            #if check_password(hashed_password, row[2]):    
            result = None
        else:
             result = "Incorrect username or password"
        cursor.close()
        cnx.close()
    else:
        result = "Unable to connect ot database"


    return result

def check_username(user):
    cnx = db.connect()[0]        
    cursor = cnx.cursor()
    query = ("SELECT * from whiley_user where username = '" + user +"'")
    cursor.execute(query)
    cursor.fetchall()
    if cursor.rowcount > 0:
        result = "Username not available"
    else:
        result = None
    cursor.close()
    cnx.close()
    return result
    
def create_username(user, passwd, email):
    #hashed_password = hash_password(passwd)
    cnx = db.connect()[0]        
    cursor = cnx.cursor()
    try:
        query = ("INSERT into whiley_user VALUES (null, %s, %s, %s)")
        cursor.execute(query, (user, passwd, email,))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
    cursor.close()
    cnx.close()


def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfill"""
    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:
        username = cherrypy.session.get(SESSION_KEY)
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    raise cherrypy.HTTPRedirect("/auth/login")
        else:
            raise cherrypy.HTTPRedirect("/auth/login")
    
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)



def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current username as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <username> is in <groupname>
        return cherrypy.request.login == 'joe' and groupname == 'admin'
    return check

def name_is(reqd_username):
    return lambda: reqd_username == cherrypy.request.login

# These might be handy

def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check

# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


# Controller to provide login and logout actions

class AuthController(object):
    
    @cherrypy.expose
    def login(self, user=None, passwd="", from_page="/"):
        if user is None:
            #return self.get_loginform("", from_page=from_page)
            template = lookup.get_template("login.html")
            error = False
            return template.render(ERROR=error)
            #raise cherrypy.HTTPRedirect("/")
        error_msg = check_credentials(user, passwd)
        if error_msg:
            error = True
            template = lookup.get_template("login.html")
            return template.render(ERRORMSG=error_msg, USERNAME=user, ERROR=error)
        else:
            cherrypy.session.regenerate()
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = user
            #return cherrypy.session[SESSION_KEY]
            raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def signup(self, user=None, passwd=None, email=None, cpasswd=None):
        #create_username("test", "ẗest", "testemail")
        if user is None or passwd is None or email is None:
            error_msg="All fields are required"
            template = lookup.get_template("signup.html")
            error = True
            return template.render(ERROR=error, ERRORMSG=error_msg, USERCREATED=False)
        elif passwd != cpasswd:
            error_msg="Passwords do not match"
            template = lookup.get_template("signup.html")
            error = True
            return template.render(ERROR=error, ERRORMSG=error_msg, USERCREATED=False)
        error_msg = check_username(user)
        if error_msg is None:
            create_username(user, passwd, email)
            template = lookup.get_template("signup.html")
            return template.render(USERCREATED=True)
        else:
            error_msg="Username already exists, choose another one"
            template = lookup.get_template("signup.html")
            error = True
            return template.render(ERROR=error, ERRORMSG=error_msg, USERCREATED=False)

    @cherrypy.expose
    def logout(self, from_page="/"):
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            #self.on_logout(username)
        raise cherrypy.HTTPRedirect(from_page or "/")

    @cherrypy.expose
    def testdb(self): 

        cnx = db.connect()[0]        
        cursor = cnx.cursor()
        query = ("SELECT username from whiley_user")
        cursor.execute(query)
        for (username) in cursor:
            print("{} name".format(username)) 
        cursor.close()
        cnx.close()