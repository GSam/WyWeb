# -*-python-*-
import mysql.connector
import cgi
from itertools import starmap
import os
from parser import st2list
import shutil
import tempfile
import subprocess
import json
import re
import glob
import random
import string

import db
import codecs
from threading import Timer

import config

import web

import cherrypy
from cherrypy.lib.static import serve_file
from cherrypy.lib.cptools import allow
from cherrypy import HTTPRedirect
from cherrypy import request

from mako.template import Template
from mako.lookup import TemplateLookup

import templating # Testing facade. 

lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================

HELLO_WORLD = """import whiley.lang.System

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
        projects = set()
        if cherrypy.session.get("_cp_username"):
            for filepath, source in files.items():
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
                            LOGGED=loggedin,
                            HELLO_WORLD=HELLO_WORLD,
                            FILES=json.dumps(files))

    index.exposed = True
    # exposed

    def student_project(self, project):
        allow(["HEAD", "GET"])
        
        # TODO This page should REALLY be secured!
        template = lookup.get_template("index.html")
        username = cherrypy.session.get("_cp_username")
        if not username:
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
                        LOGGED=username is not None,
                        FILES=json.dumps(files)
                )
    student_project.exposed = True

    # ============================================================
    # Admin Main Page
    # ============================================================
    def admin(self, *args, **kwargs):
        """
        The admin homepage should return a template for the admin page.

        >>> self = Main()
        >>> results = self.admin()
        >>> results.ERROR
        ''
        >>> results.REDIRECT
        'NO'
        >>> results.STATUS
        'DB: Connection ok'
        """
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        cnx = db.connect()

 ##       template = lookup.get_template("admin.html")
        return templating.render("admin.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, STATUS=status)

    admin.exposed = True

    # ============================================================
    # Admin Add Institutions Page
    # ============================================================

    def admin_institutions_add(self, institution=None, description=None, contact=None, website=None,
            *args, **kwargs):
        """
        Adds an institution to the database.         
        """
        allow(["HEAD", "GET", "POST"])
        options = " "
        status = ""

        if institution:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = (
                "insert into institution (institution_name,description,contact,website) values ('" +
                institution + "','" +
                description + "','" +
                contact + "','" +
                website + "')")
            cursor.execute(query)
            status = "New institution has been added"
            cursor.close()
            cnx.close()

        return templating.render("admin_institutions_add.html", ROOT_URL=config.VIRTUAL_URL, ERROR="", REDIRECT="", OPTION=options, STATUS=status)

    admin_institutions_add.exposed = True

    # ============================================================
    # Admin Institutions Page
    # ============================================================

    def admin_institutions(self, institution="", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        redirect = "NO"
        options = []

        if institution:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = ("SELECT institution_name, institutionid from institution order by institution_name")
            cursor.execute(query)
            options = list(cursor)
            cursor.close()
            cnx.close()
        displayInstitution = ""
        displayContact = ""
        displayWebsite = ""
        displayDescription = ""

        if institution == "":
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = ("SELECT institution_name, institutionid from institution order by institution_name")
            cursor.execute(query)
            institution = ""
            for (institute) in cursor:
                options.append(institute)
                if institution == "":
                    institution = institute[1]

            cursor.close()
            cnx.close()

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = (
            "SELECT institution_name,description,contact,website from institution where institutionid = '" + str(institution) + "'")
        cursor.execute(query)
        for (institution_name, description, contact, website) in cursor:
            displayInstitution = institution_name
            displayDescription = description
            displayContact = contact
            displayWebsite = website
        cursor.close()
        cnx.close()

        return templating.render("admin_institutions.html", ROOT_URL=config.VIRTUAL_URL, ERROR="", 
                               REDIRECT=redirect, OPTION=options, INSTITUTION_ID=institution,
                               INSTITUTION=displayInstitution, CONTACT=displayContact, WEBSITE=displayWebsite,
                               DESCRIPTION=displayDescription)

    admin_institutions.exposed = True

    # ============================================================
    # Admin Courses page
    # ============================================================

    def admin_courses(self, institution="", *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = []

        course_list = ""
        
        if institution:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query) 
            for (institutionid,institution_name) in cursor:
                options.append((institutionid, institution_name))
##                if str(institutionid) == institution:
##                    options = options + "<option value='" + str(institutionid) + "' selected>" + institution_name + "</option>"
##                else:
##                    options = options + "<option value='" + str(institutionid) + "'>" + institution_name + "</option>"
            cursor.close()

        if institution == "":          
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institutionid,institution_name) in cursor:
                options.append((institutionid, institution_name))
##                options = options + "<option value='" + str(institutionid) + "'>" + institution_name + "</option>" 
                if institution == "":
                    institution = str(institutionid)
            cursor.close()
                
        cnx, status = db.connect()
        cursor = cnx.cursor() 
        query = ("SELECT courseid,code from course where institutionid = '" + institution + "' order by code")
        cursor.execute(query)
        for (courseid,code) in cursor:
            course_list = course_list + "<a href=\"admin_course_details?id=" + str(courseid) + "\">" + code + "</a><br>"   
        cursor.close()

        return templating.render("admin_courses.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error,
                                REDIRECT=redirect, OPTION=options, INSTITUTION=institution, 
                                COURSE_LIST=course_list)

    admin_courses.exposed = True
    
    
        # ============================================================ 
        # Admin Add Course page 
        # ============================================================ 
    
     
    def admin_course_add(self, course_name=None, course_code=None, course_year=None, 
                        course_institution=None, validation_code=None, *args, **kwargs): 
        allow(["HEAD", "GET", "POST"]) 
        error = "" 
        redirect = "NO" 
        options = " " 
        newstatus = "" 
        validationCode = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))


        if course_code: 
            cnx, status = db.connect() 
            cursor = cnx.cursor() 
            query = ("insert into course (course_name,code,year,institutionid,validationcode) values ('" + course_name + "','" + course_code.upper() + "','" + 
                         course_year + "','" + course_institution + "','" + validation_code + "')") 
            cursor.execute(query) 
            newstatus = "New course has been added" 
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

        return templating.render("admin_courses_add.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, OPTION=options, NEWSTATUS=newstatus, VALIDATIONCODE=validationCode)  
                               
    admin_course_add.exposed = True
    

    # ============================================================
    # Admin Course details page
    # ============================================================

    def admin_course_details(self, id, *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = " "
        newstatus = "" 
        students = ""

        cnx, status = db.connect()
        cursor = cnx.cursor() 
       
        query = ("SELECT courseid,course_name,code,year,institution_name from course a, institution b where a.institutionid = b.institutionid and a.courseid = %s")
        cursor.execute(query, (id))
        for (courseid,course_name,code,year,instition_name) in cursor:
            courseName = course_name
            courseCode = code
            institution = instition_name
            courseID = courseid

        sql = "SELECT distinct a.student_info_id,a.givenname,a.surname from student_info a,student_course_link b, course c, course_stream d where c.courseid = %s and  c.courseid = d.courseid and d.coursestreamid =b.coursestreamid and b.studentinfoid = a.student_info_id"
        cursor.execute(sql, str(courseID))
        for (student_info_id,givenname,surname) in cursor:                
            students = students + web.safe(surname) + ", " + web.safe(givenname) + "</br>"
        cursor.close()
        
        return templating.render("admin_course_details.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, 
            REDIRECT=redirect, OPTION=options,
            COURSENAME=courseName, COURSECODE=courseCode, INSTITUTION=institution, STUDENTS=students)    
    admin_course_details.exposed = True
    

    # ============================================================
    # Admin Students search page
    # ============================================================

    def admin_students_search(self, searchValue="", id=None, *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        searchResult = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "
        optionsCourse = " "
        optionsStudent = " "
        searchValue = ""
        studentName = ""
        studentCourses = ""
        studentProjects = ""
        selectedValue = ""
        selectedValueCourse = ""
        whileyid = ""

        if request and request.params and 'searchValue' in request.params:
            searchValue = request.params['searchValue']
            if searchValue != "":
                cnx, status = db.connect()
                cursor = cnx.cursor()
                join = '%' + request.params['searchValue'].upper() + '%'
                sql = "select student_info_id,surname,givenname from student_info where UPPER(givenname) like %s or UPPER(surname) like %s order by surname"
                cursor.execute(sql, (join,join))
                for (students) in cursor:
                    searchResult = searchResult + "<br><a href=admin_students_search?id=" + str(students[0]) + "&searchValue=" + searchValue + ">" + web.safe(students[1]) + ", " + web.safe(students[2]) + "</a>"
                cursor.close()
                cnx.close()

        if request and request.params and 'id' in request.params:
            studentid = request.params['id']
            cnx, status = db.connect()
            cursor = cnx.cursor()
            sql = "select student_info_id,surname,givenname,institution_name,userid from student_info a,institution b where student_info_id = " + str(studentid) + " and a.institutionid = b.institutionid"
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("Error Student id = " + studentid)
                
            for (student_info_id,surname,givenname,institution_name,userid) in cursor:
                studentName = web.safe(givenname) + " " + web.safe(surname)  + " <br><h5>" + institution_name + "</h5>"
                whileyid = str(userid)
            
            sql = "select c.course_name,c.code,year,c.courseid from student_course_link a left outer join course_stream b on a.coursestreamid = b.coursestreamid left outer join course c on b.courseid = c.courseid where a.studentinfoid = " + str(studentid)
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("fail at courses")
                
            studentCourses = "<h4>Courses</h4>"
            for (courses) in cursor:
                studentCourses = studentCourses + "<a href='admin_course_details?id=" + str(courses[3]) + "'>" + courses[1] + "</a> " + str(courses[2]) + " " + str(courses[0]) + "<br>"   
            
            sql = "select projectid,project_name, filename from project, file where userid = " + str(whileyid) +" and file.projectid = project.projectid"
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("fail at projects")
                
            studentProjects = "<h4>Projects</h4>"
            projectid = ""
            for (projects, files) in cursor:
                studentProjects = studentProjects + "<a href='student_project?project=" + str(projects[0]) + "'>" + projects[1] + "</a><br>"
                studentProjects = studentProjects + " &nbsp; --> &nbsp; " + files[0] + "</a><br>" 
            cursor.close()
            cnx.close()
        
        return templating.render("admin_students_search.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, STATUS=status,
                               OPTION=options, SEARCHRESULT=searchResult, SEARCHVALUE=searchValue, STUDENTNAME=studentName,
                               STUDENTCOURSES=studentCourses, STUDENTPROJECTS=studentProjects, OPTIONCOURSE=optionsCourse, OPTIONSTUDENT=optionsStudent)

    admin_students_search.exposed = True


    # Everything else should redirect to the main page.
    def default(self, *args, **kwargs):
        raise HTTPRedirect("/")

    default.exposed = True


    # ============================================================
    # Admin Students  List page
    # ============================================================

    def admin_students_list(self, *args, **kwargs):
        allow(["HEAD", "GET", "POST"])
        error = ""
        searchResult = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = " "
        optionsCourse = " "
        optionsStudent = " "
        searchValue = ""
        studentName = "No student selected"
        studentCourses = ""
        studentProjects = ""
        selectedValue = ""
        selectedValueCourse = ""
        whileyid = ""

        if request and request.params and 'id' in request.params:
            studentid = request.params['id']
            cnx, status = db.connect()
            cursor = cnx.cursor()
            sql = "select student_info_id,surname,givenname,institution_name,userid from student_info a,institution b where student_info_id = " + str(studentid) + " and a.institutionid = b.institutionid"
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("Error Student id = " + studentid)
                
            for (student_info_id,surname,givenname,institution_name,userid) in cursor:
                studentName = web.safe(givenname) + " " + web.safe(surname)  + " <br><h5>" + institution_name + "</h5>"
                whileyid = str(userid)
            
            sql = "select c.course_name,c.code,year,c.courseid from student_course_link a left outer join course_stream b on a.coursestreamid = b.coursestreamid left outer join course c on b.courseid = c.courseid where a.studentinfoid = " + str(studentid)
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("fail at courses")
                
            studentCourses = "<h4>Courses</h4>"
            for (courses) in cursor:
                studentCourses = studentCourses + "<a href='admin_course_details?id=" + str(courses[3]) + "'>" + courses[1] + "</a> " + str(courses[2]) + " " + str(courses[0]) + "<br>"   
            
            sql = "select projectid,project_name from project where userid = " + str(whileyid)
            try:
                cursor.execute(sql)
            except mysql.connector.Error as err:
                print("fail at projects")
                
            studentProjects = "<h4>Projects</h4>"
            projectid = ""
            for (projects) in cursor:
                studentProjects = studentProjects + "<a href='#'>" + projects[1] + "</a><br>"
                projectid = str(projects[0]) 
                cursorFiles = cnx.cursor()
                sql2 = "select filename from file where projectid = %s"
                cursorFiles.execute(sql2, projectid)
                for (files) in cursorFiles:
                    studentProjects = studentProjects + " &nbsp; --> &nbsp; " + files[0] + "</a><br>"  
                cursorFiles.close()
            cursor.close()
            cnx.close()
                    
        if request and request.params and 'institution' in request.params:
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

        if request and request.params and 'course' in request.params:
            selectedValueCourse = request.params['course']               
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            sql = "SELECT courseid,code from course where institutionid = %s"
            cursor.execute(sql, selectedValue)
            for (courseid,code) in cursor:
                if str(courseid) == selectedValueCourse:
                    optionsCourse = optionsCourse + "<option value='" + str(courseid) + "' selected>" + code + "</option>"
                else:
                    optionsCourse = optionsCourse + "<option value='" + str(courseid) + "'>" + code + "</option>"
            cursor.close()   
        
        if selectedValueCourse == "": 
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            sql = "SELECT courseid,code from course where institutionid = %s"
            cursor.execute(sql, selectedValue)
            for (courseid,code) in cursor:                
                optionsCourse = optionsCourse + "<option value='" + str(courseid) + "'>" + code + "</option>" 
                if selectedValueCourse == "":
                    selectedValueCourse = str(courseid)
            cursor.close()
        
        if selectedValueCourse != "":
             cnx, status = db.connect()
             cursor = cnx.cursor() 
             sql = "SELECT distinct a.student_info_id,a.givenname,a.surname from student_info a,student_course_link b, course c, course_stream d where c.courseid = %s and  c.courseid = d.courseid and d.coursestreamid =b.coursestreamid and b.studentinfoid = a.student_info_id"
             cursor.execute(sql, selectedValueCourse)
             for (student_info_id,givenname,surname) in cursor:                
                 optionsStudent = optionsStudent + "<a href=admin_students_list?id=" + str(student_info_id) + "&institution=" + selectedValue + "&course=" + selectedValueCourse +  ">"  + web.safe(surname) + ", " + web.safe(givenname) + "</br>"
                 if selectedValueCourse == "":
                    selectedValueCourse = str(courseid)
             cursor.close()
              

        template = lookup.get_template("admin_students_list.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, STATUS=status,
                               OPTION=options, STUDENTNAME=studentName,
                               STUDENTCOURSES=studentCourses, STUDENTPROJECTS=studentProjects, OPTIONCOURSE=optionsCourse, OPTIONSTUDENT=optionsStudent)

    admin_students_list.exposed = True


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
    sql = """SELECT p.projectid FROM project p, whiley_user w WHERE w.userid = p.userid AND w.username = '""" + username + "' AND p.project_name = '" + project_name + "'"
    cursor.execute(sql)
    projectid = cursor.fetchone()
    print projectid
    if projectid is None:
        #create new project
        sql = "SELECT userid FROM whiley_user WHERE username = %s"
        cursor.execute(sql, (username,))
        userid = cursor.fetchone()[0]
        sql = "INSERT INTO project (project_name, userid) VALUES (%s, %s)"
        cursor.execute(sql, (project_name, userid))
        projectid = cursor.lastrowid


    sql = "INSERT INTO file (projectid, filename, source) VALUES (%s, %s, %s)"
    print type(projectid), type(filename), type(data)
    cursor.execute(sql, (projectid, filename, data))

def clear_files(project_name):
    username = cherrypy.session.get("_cp_username")
    cnx, status = db.connect()
    cursor = cnx.cursor()
    # Retrieve User ID
    sql =  "SELECT p.projectid FROM project p, whiley_user w WHERE w.userid = p.userid AND w.username = %s"
    cursor.execute(sql, (username,))
    projectids = cursor.fetchall()

    for (projectid,) in projectids:
        sql = "DELETE FROM file WHERE projectid = %s"
        cursor.execute(sql, (projectid,))

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

def get_project(project):
    cnx, status = db.connect()
    cursor = cnx.cursor()
    sql = """SELECT f.fileid, f.filename, p.project_name, f.source
FROM file f, project p
WHERE f.projectid = p.projectid AND p.projectid = %s"""
    cursor.execute(sql, (project,))
    result = cursor.fetchall()
    cursor.close()
    return result

def build_file_tree(filelist):
    result = []
    for fileid, filepath, project_name, source in filelist:
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
                        "type": 'project'
                      }
            result.append(project)
        
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

        # The last component should now be the file. 
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
