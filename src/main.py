# -*-python-*-

import cgi
from itertools import starmap
import os
from parser import st2list
import shutil
import tempfile
import subprocess
import json
import re

import db
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

lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================

HELLO_WORLD = """
import whiley.lang.System

method main(System.Console console):
    console.out.println("Hello World")
"""

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
        result = compile(code, verify, dir)
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

        # to start auto-save project for logged in users
        self.private_save(**files)

        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir

        result = compile_all(_main, files, _verify, dir)

        # #        shutil.rmtree(dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
        return json.dumps(response)

    compile_all.exposed = True

    def private_save(self, **files):
        if cherrypy.session.get("_cp_username"):
            for filepath, source in files.items():
                filepath = filepath.split("/")
                project = filepath.pop(0)
                save(project, "/".join(filepath)[:-len(".whiley")], source)
    private_save.exposed = True

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
        result = compile(code, "false", dir)
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

        # to start auto-save project for logged in users
        self.private_save(**files)

        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir

        result = compile_all(_main, files, _verify, dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}

            output = run(dir + os.path.dirname(_main),
                         os.path.split(_main[:-len(".whiley")])[1])
            response["output"] = output

        # shutil.rmtree(dir)
        return json.dumps(response)

    run_all.exposed = True

    # application root
    def index(self, id="HelloWorld", *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley", "utf-8")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("index.html")
        username = cherrypy.session.get("_cp_username")
        files = [
            {
                "text": "Project 1",
                "children": [
                    {
                        "text": "Hello World",
                        "data": HELLO_WORLD,
                        "type": 'file'
                    }
                ]
            }
        ]
        if username is None:
            loggedin = False
            print ("not logged in")
        else:
            loggedin = True
            print ("logged")
            filelist = get_files(username)
            files = build_file_tree(filelist)
            # print files
        return template.render(
                            ROOT_URL=config.VIRTUAL_URL,
                            CODE=code,
                            ERROR=error,
                            REDIRECT=redirect, 
                            USERNAME=username, 
                            LOGGED=loggedin,
                            HELLO_WORLD=HELLO_WORLD,
                            FILES=json.dumps(files))

    index.exposed = True
    # exposed

    # Admin Main Page
    def admin(self, id="Admin Page", *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        cnx = db.connect()

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
        return template.render(ROOT_URL=config.VIRTUAL_URL, CODE=code, ERROR=error, REDIRECT=redirect, STATUS=status)

    admin.exposed = True

    #
    # Admin Add Institutions Page
    #

    def admin_institutions_add(self, id="Admin Institutions", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        options = " "
        status = ""

        if request:
            if request.params:
                if request.params['institution']:
                    cnx, status = db.connect()
                    cursor = cnx.cursor()
                    query = (
                        "insert into institution (institution_name,description,contact,website) values ('" +
                        db.safe(request.params['institution']) + "','" +
                        db.safe(request.params['description']) + "','" +
                        db.safe(request.params['contact']) + "','" +
                        db.safe(request.params['website']) + "')")
                    cursor.execute(query)
                    status = "New institution has been added"
                    cursor.close()
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
        template = lookup.get_template("admin_institutions_add.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL, CODE=code, ERROR=error, REDIRECT=redirect, OPTION=options,
                               STATUS=status)

    admin_institutions_add.exposed = True

    #
    # Admin Institutions Page
    #

    def admin_institutions(self, id="Admin Institutions", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        redirect = "NO"
        options = " "

        selected_value = ""

        if request:
            if request.params:
                if request.params['institution']:
                    selected_value = request.params['institution']
                    cnx, status = db.connect()
                    cursor = cnx.cursor()
                    query = ("SELECT institution_name, institutionid from institution order by institution_name")
                    cursor.execute(query)
                    for (institution) in cursor:
                        if str(institution[1]) == selected_value:
                            options = options + "<option value='"+str(institution[1])+"' selected>" + institution[0] + "</option>"
                        else:
                            options = options + "<option value='"+str(institution[1])+"'>" + institution[0] + "</option>"
                    cursor.close()
                    cnx.close()
        displayInstitution = ""
        displayContact = ""
        displayWebsite = ""
        displayDescription = ""

        if selected_value == "":
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = ("SELECT institution_name, institutionid from institution order by institution_name")
            cursor.execute(query)
            selected_value = ""
            for (institution) in cursor:
                options = options + "<option value='"+str(institution[1])+"'>" + institution[0] + "</option>"
                if selected_value == "":
                    selected_value = institution[1]

            cursor.close()
            cnx.close()

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = (
            "SELECT institution_name,description,contact,website from institution where institutionid = '" + str(selected_value) + "'")
        cursor.execute(query)
        for (institution_name, description, contact, website) in cursor:
            displayInstitution = institution_name
            displayDescription = description
            displayContact = contact
            displayWebsite = website
        selected_value = ""
        cursor.close()
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
        return template.render(ROOT_URL=config.VIRTUAL_URL, CODE=code, ERROR=error, REDIRECT=redirect, OPTION=options,
                               INSTITUTION=displayInstitution, CONTACT=displayContact, WEBSITE=displayWebsite,
                               DESCRIPTION=displayDescription)

    admin_institutions.exposed = True

    #
    # Admin Courses page
    #

    def admin_courses(self, id="Admin Courses", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = " "
        selectedValue = ""

        course_list = ""
        
        if request:
            if request.params:
                if request.params['institution']:
                    selectedValue = request.params['institution']               
                    cnx, status = db.connect()
                    cursor = cnx.cursor() 
                    query = ("SELECT institutionid,institution_name from institution order by institution_name")
                    cursor.execute(query) 
                    for (institutionid,institution_name) in cursor:
                        if str(institutionid) == selectedValue:
                            options = options + "<option value='" + str(institutionid) + "' selected>" + institution_name + "</option>"
                        else:
                            options = options + "<option value='" + str(institutionid) + "'>" + institution_name + "</option>"
                    cursor.close()

        if selectedValue == "":          
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institutionid,institution_name) in cursor:
                options = options + "<option value='" + str(institutionid) + "'>" + institution_name + "</option>" 
                if selectedValue == "":
                    selectedValue = str(institutionid)
            cursor.close()
                
        cnx, status = db.connect()
        cursor = cnx.cursor() 
        query = ("SELECT courseid,code from course where institutionid = '" + selectedValue + "' order by code")
        cursor.execute(query)
        for (courseid,code) in cursor:
            course_list = course_list + "<a href=\"#\">" + code + "</a><br>"   
        cursor.close()

            
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

        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,OPTION=options,COURSE_LIST=course_list)

    admin_courses.exposed = True

    #
    # Admin Add Course page
    #

    def admin_course_add(self, id="Admin Courses", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = " "
        status = ""

        if request:
            if request.params:
                if request.params['course_code']:
                    cnx, status = db.connect()
                    cursor = cnx.cursor()
                    query = ("insert into course (course_name,code,year,institutionid) values ('" + request.params[
                        'course_name'] + "','" + request.params['course_code'] + "','" + request.params[
                                 'course_year'] + "','" + request.params['course_institution'] + "')")
                    cursor.execute(query)
                    status = "New course has been added"
                    cursor.close()
                    cnx.close()

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = ("SELECT institutionid,institution_name from institution order by institution_name")
        cursor.execute(query)
        for (institutionid, institution_name) in cursor:
            options = options + "<option value='" + str(institutionid) + "'>" + institution_name + "</option>"
        cursor.close()
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
        template = lookup.get_template("admin_courses_add.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL, CODE=code, ERROR=error, REDIRECT=redirect, OPTION=options,
                               STATUS=status)

    admin_course_add.exposed = True


    #
    # Admin Students page
    #

    def admin_students(self, id="Admin Courses", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = ("SELECT institution_name from institution order by institution_name")
        cursor.execute(query)
        for (institution) in cursor:
            options = options + "<option>" + institution[0] + "</option>"
        cursor.close()
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
        return template.render(ROOT_URL=config.VIRTUAL_URL, CODE=code, ERROR=error, REDIRECT=redirect, STATUS=status,
                               OPTION=options)

    admin_students.exposed = True


    # Everything else should redirect to the main page.
    def default(self, *args, **kwargs):
        raise HTTPRedirect("/")

    default.exposed = True


# ============================================================
# Compiler Interface
# ============================================================

# Load a given JSON file from the filesystem
def load(filename, encoding):
    f = codecs.open(filename, "r", encoding)
    data = f.read()
    f.close()
    return data


# Save a given file to the filesystem
def save(project_name, filename, data):
    username = cherrypy.session.get("_cp_username")
    cnx, status = db.connect()
    cursor = cnx.cursor()
    sql = """SELECT p.projectid FROM project p, whiley_user w WHERE w.userid = p.userid AND w.username = '""" + username + "'"
    cursor.execute(sql)
    projectid = cursor.fetchone()[0]

    sql = "INSERT INTO file (projectid, filename, source) VALUES (%s, %s, %s)"
    cursor.execute(sql, (projectid, filename, data))

    return


def save_all(files, dir):
    for filename, contents in files.items():
        filepath = dir + "/" + filename
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        with codecs.open(filepath, 'w', 'utf8') as f:
            f.write(contents)


def get_files(user):
    cnx, status = db.connect()
    cursor = cnx.cursor()
    sql = """SELECT f.fileid, f.filename, p.project_name, f.source
FROM file f, project p, whiley_user w
WHERE f.projectid = p.projectid AND p.userid = w.userid AND w.username = '""" + user + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    return result

def build_file_tree(filelist):
    result = []
    for fileid, filepath, project_name, source in filelist:
        project = None
        for project_ in result:
            if project_["text"] == project_name:
                project = project_
                break

        if not project:
            project = {
                        "text": project_name,
                        "children": [],
                      }
            result.append(project)
        
        for component in filepath.split("/"):
            subdir = None
            for child in project['children']:
                if child["text"] == component:
                    subdir = child
                    break

            if not subdir:
                subdir = {
                        "text": component,
                        "children": [],
                      }
                project['children'].append(subdir)
            project = subdir

        project['data'] = source
        project['type'] = "file"

    return result

# Compile a snippet of Whiley code.  This is done by saving the file
# to disk in a temporary location, compiling it using the Whiley2Java
# Compiler and then returning the compilation output.
def compile(code, verify, dir):
    filename = dir + "/tmp.whiley"
    # set required arguments
    args = [
        config.JAVA_CMD,
        "-jar",
        config.WYJC_JAR,
        "-bootpath", config.WYRT_JAR,  # set bootpath
        "-whileydir", dir,  # set location of Whiley source file(s)
        "-classdir", dir,  # set location to place class file(s)
        "-brief"  # enable brief compiler output (easier to parse)
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
    filename = dir + main
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
    # print("DEBUG:", " ".join(args))

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
        # print("DEBUG:", [
        # config.JAVA_CMD,
        #    "-Djava.security.manager",
        #    "-Djava.security.policy=whiley.policy",
        #    "-cp",config.WYJC_JAR + ":" + dir,
        #    main
        #    ])
        # run the JVM
        proc = subprocess.Popen([
                                    config.JAVA_CMD,
                                    "-Djava.security.manager",
                                    "-Djava.security.policy=whiley.policy",
                                    "-cp", config.WYJC_JAR + ":" + dir,
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
    dir = tempfile.mkdtemp(prefix="", dir=config.DATA_DIR)
    tail, head = os.path.split(dir)
    return head
