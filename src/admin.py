import cherrypy, config, web
import templating, db
from cherrypy.lib.cptools import allow

# TODO Remove these imports
import mysql.connector
from cherrypy import request

from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['html'])

class Admin(object):
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
        import random, string
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
