# -*-python-*-
import cgi
import os
import shutil
import tempfile
import subprocess
import json
import re
import glob
import codecs
from threading import Timer

import cherrypy
from cherrypy.lib.static import serve_file
from cherrypy.lib.cptools import allow
from cherrypy import HTTPRedirect
from mako.lookup import TemplateLookup

import db
import config
import auth
import admin


lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================

HELLO_WORLD = """import whiley.lang.System

method main(System.Console console):
    console.out.println("Hello World")
"""

class Main(admin.Admin):
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
        projects = set()
        if cherrypy.session.get(auth.SESSION_USERID):
            for filepath, source in files.items():
                print filepath
                filepath = filepath.split("/")
                project = filepath.pop(0)
                
                # clear existing files in project
                if project not in projects:
                    clear_files(project)
                    projects.add(project)

                # save
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

    def run_all(self, _verify, _main, _project, *args, **files):
        allow(["HEAD", "POST"])

        # to start auto-save project for logged in users
        self.private_save(**files)

        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir

        # Find package name
        package = None
        main_src = files[_main].strip()
        if main_src.startswith('package'):
            first_line = main_src.split('\n')[0]
            package = first_line.replace('package', '').strip()

        run_path = os.path.join(dir, os.path.dirname(_main))

        result = compile_all(_main, files, _verify, dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
            class_to_run = os.path.split(_main[:-len(".whiley")])[1].replace('/','.')
            if package:
                class_to_run = package + '.' + class_to_run
                run_path = os.path.join(dir, _project)

            output = run(run_path, class_to_run)
            response["output"] = output

        # shutil.rmtree(dir)
        return json.dumps(response)

    run_all.exposed = True

    # ============================================================
    # application root
    # ============================================================
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
        username = cherrypy.session.get(auth.SESSION_KEY)
        userid = cherrypy.session.get(auth.SESSION_USERID)
        files = [
            {
                "text": "Project 1",
                "children": [
                    {
                        "text": "Hello World",
                        "data": HELLO_WORLD,
                        "type": 'file'
                    }
                ],
                "type": 'project'
            }
        ]
        if username is None:
            loggedin = False
            print ("not logged in")
        else:
            loggedin = True
            print ("logged")
            filelist = get_files(username)
            print filelist
            files = build_file_tree(filelist)
            # print files
        return template.render(
                            ROOT_URL=config.VIRTUAL_URL,
                            CODE=code,
                            ERROR=error,
                            REDIRECT=redirect, 
                            USERNAME=username, 
                            USERID=userid, 
                            LOGGED=loggedin,
                            HELLO_WORLD=HELLO_WORLD,
                            FILES=json.dumps(files))

    index.exposed = True
    # exposed

    def student_project(self, project):
        allow(["HEAD", "GET"])
        
        # TODO This page should REALLY be secured!
        template = lookup.get_template("index.html")
        username = cherrypy.session.get(auth.SESSION_KEY)
        userid = cherrypy.session.get(auth.SESSION_USERID)
        if not userid:
            raise cherrypy.HTTPError(403, "Unauthorised!")
        files = get_project(project)
        print files
        files = build_file_tree(files)
        return template.render(
                        ROOT_URL=config.VIRTUAL_URL,
                        CODE="",
                        ERROR="",
                        REDIRECT="",
                        USERNAME=username,
                        USERID=userid,
                        LOGGED=username is not None,
                        FILES=json.dumps(files)
                )
    student_project.exposed = True


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
    userid = cherrypy.session.get(auth.SESSION_USERID)
    cnx, status = db.connect()
    cursor = cnx.cursor()
    print "saving Project:", project_name, filename
    sql = "SELECT p.projectid FROM project p where p.userid = %s AND p.project_name = %s"
    cursor.execute(sql, (userid,project_name))
    project = cursor.fetchone()
    if project:
        projectid = project[0]
        print projectid
        if projectid is None:
            sql = "INSERT INTO project (project_name, userid) VALUES (%s, %s)"
            cursor.execute(sql, (project_name, userid))
            projectid = cursor.lastrowid


        sql = "INSERT INTO file (projectid, filename, source) VALUES (%s, %s, %s)"
        print projectid, filename, data
        print sql
        cursor = cnx.cursor()
        cursor.execute(sql, (projectid, filename, data))
        if cursor.fetchwarnings():
            for item in cursor.fetchwarnings():
                print item
        cursor.close()
        cursor = cnx.cursor()
        cursor.execute("select * from file where projectid = %s", (projectid, ))
        print cursor.fetchall()

def clear_files(project_name):
    print "CLEAR FILES", project_name
    userid = cherrypy.session.get(auth.SESSION_USERID)
    cnx, status = db.connect()
    cursor = cnx.cursor()
    # Retrieve User ID
    sql =  "SELECT p.projectid FROM project p WHERE p.userid = %s and p.project_name = %s"
    cursor.execute(sql, (userid,project_name))
    projectids = cursor.fetchall()

    for (projectid,) in projectids:
        sql = "DELETE FROM file WHERE projectid = %s"
        cursor.execute(sql, (projectid,))

def save_all(files, dir):
    for filename, contents in files.items():
        filepath = dir + "/" + filename
        print filepath
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        with codecs.open(filepath, 'w', 'utf8') as f:
            f.write(contents)


def get_files(user):
    cnx, status = db.connect()
    cursor = cnx.cursor()
    sql = """SELECT f.fileid, f.filename, p.projectid, p.project_name, f.source
            FROM whiley_user w
            left outer join project p on (p.userid = w.userid)
            left outer join file f on (f.projectid = p.projectid)
            WHERE w.username = '""" + user + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    return result

def get_project(project):
    cnx, status = db.connect()
    cursor = cnx.cursor()
    sql = """SELECT f.fileid, f.filename, p.projectid, p.project_name, f.source
            FROM file f, project p
            WHERE f.projectid = p.projectid AND p.projectid = %s"""
    cursor.execute(sql, (project,))
    result = cursor.fetchall()
    cursor.close()
    return result

def build_file_tree(filelist):
    result = []
    for fileid, filepath, projectid, project_name, source in filelist:
        # find the project
        project = None
        for project_ in result:
            if project_["text"] == project_name:
                project = project_
                break

        if not project:
            project = {
                        "text": project_name,
                        "children": [],
                        "type": 'project',
                        "projectid": projectid
                      }
            result.append(project)

        if filepath:
            lastComponent = None
            # for each path component ...
            for component in filepath.split("/"):
                # Find/create it.
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
                lastComponent = subdir

            # The last component should now be the file.
            lastComponent['data'] = source
            lastComponent['type'] = "file"
            lastComponent['fileid'] = fileid

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
        # Configure Timeout
        kill_proc = lambda p: p.kill()
        timer = Timer(15, kill_proc, [proc])
        timer.start()
        # Run process        
        (out, err) = proc.communicate()
        timer.cancel()
        # Check what happened
        if proc.returncode < 0:
            return [{
                "filename": "",
                "line": "",
                "start": "",
                "end": "",
                "text": "Compiling / Verifying your program took too long!"
            }]
        # Continue
        if err == None:
            return splitErrors(out)
        else:
            return splitErrors(err)
    except Exception as ex:
        # error, so return that
        return "Compile Error: " + str(ex)


def compile_all(main, files, verify, dir):
    filename = os.path.join(dir, main)
    print filename
    save_all(files, dir)
    args = [
        config.JAVA_CMD,
        "-jar",
        config.WYJC_JAR,
        "-bootpath", config.WYRT_JAR,
        "-whileydir"] + glob.glob(os.path.join(dir, "*")) + [
        "-classdir"] + glob.glob(os.path.join(dir, "*")) + [
        "-brief"
    ]

    if verify == "true":
        args.append("-verify")

    list_files = [os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in files if f.endswith('.whiley')]

    args += list_files
    # print("DEBUG:", " ".join(args))

    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        # Configure Timeout
        kill_proc = lambda p: p.kill()
        timer = Timer(15, kill_proc, [proc])
        timer.start()
        # Run process        
        (out, err) = proc.communicate()
        timer.cancel()
        # Check what happened
        if proc.returncode < 0:
            return [{
                "filename": "",
                "line": "",
                "start": "",
                "end": "",
                "text": "Compiling / Verifying your program took too long!"
            }]
        # Continue
        if err == None:
            return splitErrors(out)
        else:
            return splitErrors(err)
    except Exception as ex:
        # error, so return that
        return "Compile Error: " + str(ex)


def run(dir, main="tmp"):
    try:
        ##print("DEBUG:", [
        ## config.JAVA_CMD,
        ##    "-Djava.security.manager",
        ##    "-Djava.security.policy=whiley.policy",
        ##    "-cp",config.WYJC_JAR + ":" + dir,
        ##    main
        ##    ])
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

