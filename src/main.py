# -*-python-*-

import cgi
import os
import shutil
import tempfile
import subprocess
import json
import re

import mysql.connector
import codecs
from threading import Timer

import config

import cherrypy
from cherrypy.lib.static import serve_file
from cherrypy.lib.cptools import allow
from cherrypy import HTTPRedirect
from cherrypy import request

from mako.template import Template
from mako.lookup import TemplateLookup

from mysql.connector import errorcode

lookup = TemplateLookup(directories=['html'])

import mysql.connector
from mysql.connector import errorcode

# ============================================================
# Application Entry
# ============================================================

def connect(thread_index):
    cherrypy.thread_data.db = mysql.connector.connect(host="kipp-cafe.ecs.vuw.ac.nz", user="whiley", database="whiley", passwd="coyote")

cherrypy.engine.subscribe('start_thread', connect)

class Main(object):

    # gives access to images/
    def images(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("images/" + filename)
        return serve_file(abspath, "image/png")
    images.exposed = True

    def js(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("js/" + filename)
        return serve_file(abspath, "application/javascript")
    js.exposed = True

    def css(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("css/" + filename)
        return serve_file(abspath, "text/css")
    css.exposed = True

    def compile(self, code, verify, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir
        # Second, compile the code
        result = compile(code,verify,dir)
        # Third, delete working directory
        shutil.rmtree(dir)
        # Fouth, return result as JSON
        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
        return json.dumps(response)
    compile.exposed = True

    def compile_all(self, _verify, _main, *args, **files):
        allow(["HEAD", "POST"])

        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir

        result = compile_all(_main, files, _verify, dir)

        shutil.rmtree(dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
        return json.dumps(response)
    compile_all.exposed = True

    def save(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        # Second, save the file
        save(config.DATA_DIR + "/" + dir + "/tmp.whiley", code, "utf-8")
        # Fouth, return result as JSON
        return json.dumps({
            "id": dir
        })
    save.exposed = True

    def run(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir
        # Second, compile the code and then run it
        result = compile(code,"false",dir)
        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
            # Run the code if the compilation succeeded.
            output = run(dir)
            response["output"] = output
        # Third, delete working directory
        shutil.rmtree(dir)
        # Fourth, return result as JSON
        return json.dumps(response)
    run.exposed = True

    def run_all(self, _verify, _main, *args, **files):
        allow(["HEAD", "POST"])

        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir

        result = compile_all(_main, files, _verify, dir)

        shutil.rmtree(dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}

            output = run(dir, _main)
            response["output"] = output
        return json.dumps(response)

    # application root
    def index(self, id="HelloWorld", *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley","utf-8")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("index.html")
        username = cherrypy.session.get("_cp_username")
        if username is None:
            loggedin = False
            print ("not logged in")
        else:
            loggedin = True
            print ("logged")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect, USERNAME=username, LOGGED=loggedin)
    index.exposed = True
    # exposed

    #Admin Main Page
    def admin(self, id="Admin Page", *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        try:
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                status = "Something is wrong with your user name or password"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                status = "Database does not exists"
            else:
                status = err
        else:
            cnx.close()
        
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("admin.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,STATUS=status)
    admin.exposed = True
    
    #Admin Main Page
    def admin_institutions(self, id="Admin Institutions", *args, **kwargs):
        allow(["HEAD", "GET","POST"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "

        try:
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                status = "Something is wrong with your user name or password"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                status = "Database does not exists"
            else:
                status = err
        else:
            cnx.close()        
        
        if request:
            if request.params:
                if request.params['institution']:
                    try:
                       cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')        
                       cursor = cnx.cursor()
                       query = ("insert into institution (institution_name) values ('" + request.params['institution'] + "')")
                       cursor.execute(query)
                       cnx.commit()
                       cursor.close()
                       cnx.close()
                    except mysql.connector.Error as err:
                       if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                           status = "Something is wrong with your user name or password"
                       elif err.errno == errorcode.ER_BAD_DB_ERROR:
                           status = "Database does not exists"
                       else:
                           status = err
                    else:
                       cnx.close() 

        try:    
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')        
            cursor = cnx.cursor()
            query = ("SELECT institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institution) in cursor:
                options = options + "<option>" + institution[0] + "</option>"   
            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            status = err
        else:
            cnx.close() 
                
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("admin_institutions.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,STATUS=status,OPTION=options)
    admin_institutions.exposed = True

    #Admin Courses page
    def admin_courses(self, id="Admin Courses", *args, **kwargs):
        allow(["HEAD", "GET","POST"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "

        try:
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                status = "Something is wrong with your user name or password"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                status = "Database does not exists"
            else:
                status = err
        else:
            cnx.close()        
        try:    
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')        
            cursor = cnx.cursor()
            query = ("SELECT institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institution) in cursor:
                options = options + "<option>" + institution[0] + "</option>"   
            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            status = err
        else:
            cnx.close() 
                
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("admin_courses.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,STATUS=status,OPTION=options)
    admin_courses.exposed = True

    #Admin Courses page
    def admin_students(self, id="Admin Courses", *args, **kwargs):
        allow(["HEAD", "GET","POST"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "

        try:
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                status = "Something is wrong with your user name or password"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                status = "Database does not exists"
            else:
                status = err
        else:
            cnx.close()        
        try:    
            cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')        
            cursor = cnx.cursor()
            query = ("SELECT institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institution) in cursor:
                options = options + "<option>" + institution[0] + "</option>"   
            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            status = err
        else:
            cnx.close() 
                
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("admin_students.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,STATUS=status,OPTION=options)
    admin_students.exposed = True


    # Everything else should redirect to the main page.
    def default(self, *args, **kwargs):
        raise HTTPRedirect("/")
    default.exposed = True

# ============================================================
# Compiler Interface
# ============================================================

# Load a given JSON file from the filesystem
def load(filename,encoding):
    f = codecs.open(filename,"r",encoding)
    data = f.read()
    f.close()
    return data

# Save a given file to the filesystem
def save(filename,data,encoding):
    f = codecs.open(filename,"w",encoding)
    f.write(data)
    f.close()
    try:
        data = open(filename, "rb").read()
        cursor = cherrypy.thread_data.db.cursor()
        sql = "INSERT INTO file (projectid, filename, source) VALUES ('1','text', %s)"
        cursor.execute(sql, (data,))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
    return

def save_all(files, dir):
    for filename, contents in files.items():
        with open(dir + "/" + filename) as f:
            f.write(contents)

# Compile a snippet of Whiley code.  This is done by saving the file
# to disk in a temporary location, compiling it using the Whiley2Java
# Compiler and then returning the compilation output.
def compile(code,verify,dir):

    filename = dir + "/tmp.whiley"
    # set required arguments
    args = [
            config.JAVA_CMD,
            "-jar",
            config.WYJC_JAR,
            "-bootpath", config.WYRT_JAR, # set bootpath
            "-whileydir", dir,     # set location of Whiley source file(s)
            "-classdir", dir,      # set location to place class file(s)
            "-brief"              # enable brief compiler output (easier to parse)
        ]
    # Configure optional arguments
    if verify == "true":
        args.append("-verify")
    # save the file
    save(filename, code, "utf-8")
    args.append(filename)
    # run the compiler
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        (out, err) = proc.communicate()
        if err == None:
            return splitErrors(out)
        else:
            return splitErrors(err)
    except Exception as ex:
        # error, so return that
        return "Compile Error: " + str(ex)

def compile_all(main, files, verify, dir):
    filename = dir + "/" + main
    args = [
            config.JAVA_CMD,
            "-jar",
            config.WYJC_JAR,
            "-bootpath", config.WYRT_JAR,
            "-whileydir", dir,
            "-classdir", dir,
            "-brief"
        ]

    if verify == "true":
        args.append("-verify")

    save_all(files, dir)
    args.append(filename)

    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        out, err = proc.communicate()
        if err == None:
            return splitErrors(out)
        else:
            return splitErrors(err)
    except Exception as ex:
        return "Compile Error: " + str(ex)

def run(dir, main="tmp"):
    try:
        # run the JVM
        proc = subprocess.Popen([
            config.JAVA_CMD,
            "-Djava.security.manager",
            "-Djava.security.policy=whiley.policy",
            "-cp",config.WYJC_JAR + ":" + dir,
            main
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        # Configure Timeout
        kill_proc = lambda p: p.kill()
        timer = Timer(20, kill_proc, [proc])
        timer.start()
        # Run process        
        (out, err) = proc.communicate()
        timer.cancel()
        # Check what happened
        if proc.returncode >= 0:
            return out
        else:
            return "Timeout: Your program ran for too long!"
    except Exception as ex:
        # error, so return that
        return "Run Error: " + str(ex)

# Split errors output from WyC into a list of JSON records, each of
# which includes the filename, the line number, the column start and
# end, as well a the text of the error itself.
def splitErrors(errors):
    r = []
    for err in errors.split("\n"):
        if err != "":
            r.append(splitError(err))
    return r

def splitError(error):
    parts = error.split(":", 4)
    if len(parts) == 5:
        return {
            "filename": parts[0],
            "line": int(parts[1]),
            "start": int(parts[2]),
            "end": int(parts[3]),
            "text": parts[4]
        }
    else:
        return {
            "filename": "",
            "line": "",
            "start": "",
            "end": "",
            "text": error
        }

# Get the working directory for this request.
def createWorkingDirectory():
    dir = tempfile.mkdtemp(prefix="",dir=config.DATA_DIR)
    tail,head = os.path.split(dir)
    return head
