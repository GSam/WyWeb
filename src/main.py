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
from cherrypy._cperror import HTTPError
from mako.lookup import TemplateLookup

import db
import config
import auth
import admin
from auth import isAdmin, isTeacher
import tarfile

lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================
DEFAULT_PROJECT = [
            {
                "text": "Samples",
                "children": [
                    {
                        "text": "HelloWorld",
                        "data": """import whiley.lang.System

method main(System.Console console):
    console.out.println("Hello World")
""",
                        "type": 'file'
                    },
                    {
                        "text": "abs",
                        "data": """import whiley.lang.*

/**
* Return the absolute of an integer parameter
*/
function abs(int x) => (int y)
// Return value cannot be negative
ensures y >= 0:
    //
    if x >= 0:
        return x
    else:
        return -x

public method main(System.Console console):
    console.out.println("abs(1) = " ++ abs(1))
    console.out.println("abs(0) = " ++ abs(0))
    console.out.println("abs(-1) = " ++ abs(-1))""",
                        "type": 'file'
                    },
                    {
                        "text": "max",
                        "data": """import whiley.lang.*

/**
* The max() function, which returns the greater
* of two integer arguments
*/
function max(int x, int y) => (int r)
// result must be one of the arguments
ensures r == x || r == y
// result must be greater-or-equal than arguments
ensures r >= x && r >= y:
//
    if x > y:
        return x
    else:
        return y

method main(System.Console console):
    console.out.println("max(10,0) = " ++ max(10,0))
    console.out.println("max(5,6) = " ++ max(5,6))
    console.out.println("max(0,0) = " ++ max(0,0))""",
                        "type": 'file'
                    },
                    {
                        "text": "microwave",
                        "data": """// This is based on the classical "microwave" oven state
// machine problem. The purpose is to ensure that the
// door is never open when the microwave is heating.

type nat is (int x) where x >= 0

// First, define the state of the microwave.
type Microwave is {
    bool heatOn, // if true, the oven is cooking
    bool doorOpen, // if true, the door is open
    nat timer // timer setting (in seconds)
} where !doorOpen || !heatOn

// The clock tick event is signaled by the internal clock
// circuits of the microwave. It is triggered every second
// in order to implement timed cooking.
function clockTick(Microwave m) => Microwave:
    //
    if m.heatOn && m.timer == 0:
        // Timer has expired
        m.heatOn = false
    else if m.heatOn:
        // Still time left
        m.timer = m.timer - 1
    // If heating is not on, then ignore this event
    return m

// Set the timer on the microwave. This can't be done if
// the microwave is cooking.
function setTimer(Microwave m, nat value) => Microwave
requires !m.heatOn:
    //
    m.timer = value
    return m

// Signals that the "start cooking" button has been
// pressed. Observe that, if the door is open, then
// this event should have no effect.
function startCooking(Microwave m) => Microwave:
    //
    // Here, we check the all important safety propery
    // for the microwave.
    if !m.doorOpen:
        m.heatOn = true
    return m

// A door closed event is triggered when the sensor
// detects that the door is closed.
function doorClosed(Microwave m) => Microwave
requires m.doorOpen:
//
    m.doorOpen = false
    return m

// A door opened event is triggered when the sensor
// detects that the door is opened.
function doorOpened(Microwave m) => Microwave
requires !m.doorOpen:
    //
    m.doorOpen = true
    m.heatOn = false
    return m""",
                        "type": 'file'
                    }
                ],
                "type": 'project'
            }
        ]

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
        suffix = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + suffix

        result = compile_all(_main, files, _verify, dir)

        shutil.rmtree(dir)

        if "internal failure (null)" in str(result):
            make_tarfile('%s.tar.gz' % suffix, dir)

        if type(result) == str:
            response = {"result": "error", "error": result}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
        return json.dumps(response)

    compile_all.exposed = True

    def private_delete_project(self, _project, **files):
        projects = set()
        if cherrypy.session.get(auth.SESSION_USERID):
            delete_project(_project)
    private_delete_project.exposed = True

    def private_rename_project(self, _project, _new_name, **files):
        projects = set()
        if cherrypy.session.get(auth.SESSION_USERID):
            rename_project(_project, _new_name)
    private_rename_project.exposed = True

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
        return json.dumps({"result": "success"})
    private_save.exposed = True

    def save(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        # Second, save the file

        f = codecs.open(config.DATA_DIR + "/" + dir + "/tmp.whiley","w",'utf-8')
        f.write(code)
        f.close()

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
        suffix = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + suffix

        # Find package name
        package = None
        main_src = files[_main].strip()
        if main_src.startswith('package'):
            first_line = main_src.split('\n')[0]
            package = first_line.replace('package', '').strip()

        run_path = os.path.join(dir, os.path.dirname(_main))

        result = compile_all(_main, files, _verify, dir)

        if "internal failure (null)" in str(result):
            make_tarfile('%s.tar.gz' % suffix, dir)

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

        shutil.rmtree(dir)
        return json.dumps(response)

    run_all.exposed = True

    # ============================================================
    # application root
    # ============================================================
    def index(self, *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        admin = False

        template = lookup.get_template("index.html")
        username = cherrypy.session.get(auth.SESSION_KEY)
        userid = cherrypy.session.get(auth.SESSION_USERID)
        files = DEFAULT_PROJECT

        if userid is None:
            loggedin = False
            print ("not logged in")
        else:
            loggedin = True
            if isAdmin(userid) or isTeacher(userid):
                admin = True
            print ("logged")
            filelist = get_files(username)
            print filelist
            files = build_file_tree(filelist)
            # print files
        return template.render(
                            ROOT_URL=config.VIRTUAL_URL,
                            ERROR=error,
                            REDIRECT=redirect, 
                            USERNAME=username, 
                            USERID=userid, 
                            LOGGED=loggedin,
                            ADMIN=admin,
                            FILES=json.dumps(files))

    index.exposed = True
    # exposed

    def view_project(self, userid, projectname):
        allow(["HEAD", "GET"])

        cnx, status = db.connect()
        cursor = cnx.cursor()
        sql = "SELECT p.projectid FROM project p where p.userid = %s AND p.project_name = %s"
        cursor.execute(sql, (userid, projectname))
        result = cursor.fetchone()
        print result        
        if not result:
            raise HTTPError(404)
        result = result[0]

        return self.student_project(result)
    view_project.exposed = True

    def student_project(self, project):
        allow(["HEAD", "GET"])
        admin = False
        # TODO This page should REALLY be secured! How should this work?
        template = lookup.get_template("index.html")
        username = cherrypy.session.get(auth.SESSION_KEY)
        userid = cherrypy.session.get(auth.SESSION_USERID)

        if isAdmin(userid):
            admin = True
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
                        ADMIN=admin,
                        FILES=json.dumps(files)
                )
    student_project.exposed = True

    def exports(self, _main, *args, **files):
        import StringIO

        allow(["HEAD", "POST", "GET"])
        
        # First, create working directory
        suffix = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + suffix

        save_all(files, dir)

        output = make_tarfile("%s.tar.gz" % _main.split("/")[0], os.path.join(dir, _main.split("/")[0]))

        tempf = open(output, 'rb')
        stringf = StringIO.StringIO(tempf.read())
        tempf.close()

        result = cherrypy.lib.static.serve_fileobj(stringf, "application/x-tgz", name="this")
        os.unlink(output)
        return result

    exports.exposed = True

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
    print "saving Project:", project_name, userid
    sql = "SELECT p.projectid FROM project p where p.userid = %s AND p.project_name = %s"
    cursor.execute(sql, (userid,project_name))
    project = cursor.fetchone()
    if project:
        projectid = project[0]
    else:
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

def delete_project(project_name):
    print "DELETE PROJECT", project_name
    userid = cherrypy.session.get(auth.SESSION_USERID)
    cnx, status = db.connect()
    cursor = cnx.cursor()
    # Retrieve User ID
    sql = "SELECT p.projectid FROM project p WHERE p.userid = %s and p.project_name = %s"
    cursor.execute(sql, (userid,project_name))
    projectids = cursor.fetchall()

    for (projectid,) in projectids:
        sql = "DELETE FROM file WHERE projectid = %s"
        cursor.execute(sql, (projectid,))

    for (projectid,) in projectids:
        sql = "DELETE FROM project WHERE projectid = %s"
        cursor.execute(sql, (projectid,))


def rename_project(old_name, new_name):
    print "RENAME PROJECT", old_name
    userid = cherrypy.session.get(auth.SESSION_USERID)
    cnx, status = db.connect()
    cursor = cnx.cursor()
    # Retrieve User ID
    sql = "SELECT p.projectid FROM project p WHERE p.userid = %s and p.project_name = %s"
    cursor.execute(sql, (userid,old_name))
    projectids = cursor.fetchall()

    for (projectid,) in projectids:
        sql = "UPDATE project SET project_name = %s WHERE projectid = %s"
        cursor.execute(sql, (new_name, projectid))


def clear_files(project_name):
    print "CLEAR FILES", project_name
    userid = cherrypy.session.get(auth.SESSION_USERID)
    cnx, status = db.connect()
    cursor = cnx.cursor()
    # Retrieve User ID
    sql = "SELECT p.projectid FROM project p WHERE p.userid = %s and p.project_name = %s"
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

def make_tarfile(output_filename, source_dir):
    if not os.path.exists(config.FAIL_DIR):
        os.makedirs(config.FAIL_DIR)

    output = os.path.join(config.FAIL_DIR, output_filename)
    with tarfile.open(output, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

    return output
