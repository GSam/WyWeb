import cherrypy, config, web
import templating, db
from cherrypy.lib.cptools import allow
import auth
from auth import AuthController, requireAdmin

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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)
        
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        cnx = db.connect()

        return templating.render("admin.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, STATUS=status)
    admin.exposed = True

    # ============================================================
    # Manage admin page
    # ============================================================
    def manage_admins(self, newadminid="", deleteadminid="", searchuser=None, *args, **kwargs):
        """
        Manage the admins.

        >>> self = manage_admins()
        >>> results = manage_admins()
        >>> results.ERROR
        ''
        >>> results.REDIRECT
        'NO'
        >>> results.STATUS
        'DB: Connection ok'
        """
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        message = ""
        redirect = "NO"
        adminList = []
        userList = []

        if deleteadminid is not None:
            print deleteadminid

        if newadminid == "":          
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT username, user.userid from whiley_user user, admin_users admin  where user.userid=admin.userid")
            cursor.execute(query)
            for (username, userid) in cursor:
                adminList.append((username,userid))
            cursor.close()
            userid = None

        if searchuser is not None:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT userid from whiley_user  where username=%s")
            cursor.execute(query,(searchuser,))
            userid = cursor.fetchone()
            if cursor.rowcount > 0:
                if not auth.create_admin(userid[0]):
                    message = "User is an Admin already"
            else:
                message = "User does not exist"
            cursor.close()

        return templating.render("manage_admins.html", ADMINLIST=adminList, MESSAGE=message)

    manage_admins.exposed = True

    # ============================================================
    # Admin Add Institutions Page
    # ============================================================

    def admin_institutions_add(self, institution=None, description=None, contact=None, website=None,
            *args, **kwargs):
        """
        Adds an institution to the database.         
        """
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

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
        displayInstitution, displayDescription, displayContact, displayWebsite = cursor.fetchone()
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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = []

        course_list = []
        
        if institution:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query) 
            options = list(cursor)
            cursor.close()

        if institution == "":          
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institutionid,institution_name) in cursor:
                options.append((institutionid, institution_name))
                if institution == "":
                    institution = str(institutionid)
            cursor.close()
                
        cnx, status = db.connect()
        cursor = cnx.cursor() 
        query = ("SELECT courseid,code from course where institutionid = '" + institution + "' order by code")
        cursor.execute(query)
        course_list = list(cursor)
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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        import random, string
        allow(["HEAD", "GET", "POST"]) 
        error = "" 
        redirect = "NO" 
        options = []
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
        options = list(cursor)
        cursor.close() 
        cnx.close() 

        return templating.render("admin_courses_add.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect, OPTION=options, NEWSTATUS=newstatus, VALIDATIONCODE=validationCode)  
                               
    admin_course_add.exposed = True
    

    # ============================================================
    # Admin Course details page
    # ============================================================

    def admin_course_details(self, id, *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = " "
        newstatus = "" 
        students = []

        cnx, status = db.connect()
        cursor = cnx.cursor() 
       
        query = ("SELECT courseid,course_name,code,year,validationcode,institution_name from course a, institution b where a.institutionid = b.institutionid and a.courseid = %s")
        cursor.execute(query, (id,))
        courseID, courseName, courseCode, year, validationcode, institution = cursor.fetchone()

        sql = "SELECT distinct a.student_info_id,a.givenname,a.surname from student_info a,student_course_link b, course c, course_stream d where c.courseid = %s and  c.courseid = d.courseid and d.coursestreamid =b.coursestreamid and b.studentinfoid = a.student_info_id"

        cursor.execute(sql, (str(courseID),))
        students = [name(givenname, surname) for _, givenname, surname in cursor]

        cursor.close()
        
        return templating.render("admin_course_details.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, 
            REDIRECT=redirect, OPTION=options,
            COURSENAME=courseName, COURSECODE=courseCode, YEAR=year, VALIDATIONCODE=validationcode,
            INSTITUTION=institution, STUDENTS=students)
    admin_course_details.exposed = True
    

    # ============================================================
    # Admin Students search page
    # ============================================================

    def admin_students_search(self, searchValue="", id=None, *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        error = ""
        searchResult = []
        redirect = "NO"
        status = "DB: Connection ok"
        studentName = ""
        institutionName = ""
        studentCourses = []
        studentProjects = []
        whileyid = ""

        if searchValue:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            join = '%' + searchValue.upper() + '%'
            sql = "select student_info_id,surname,givenname from student_info where UPPER(givenname) like %s or UPPER(surname) like %s order by surname"
            cursor.execute(sql, (join,join))
            searchResult = [(id_, web.safe(surname) + ", " + web.safe(givenname)) 
                            for id_, surname, givenname in cursor]
            cursor.close()
            cnx.close()

        if id:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            sql = "select student_info_id,surname,givenname,institution_name,userid from student_info a left outer join institution b on (a.institutionid = b.institutionid) where student_info_id = " + str(id)
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print("Error Student id = " + str(id))
                
            _, surname, givenname, institutionName, userid = cursor.fetchone()
            studentName = fullname(givenname, surname)
            whileyid = str(userid)
            
            sql = "select c.course_name,c.code,year,c.courseid from student_course_link a left outer join course_stream b on a.coursestreamid = b.coursestreamid left outer join course c on b.courseid = c.courseid where a.studentinfoid = " + str(id)
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print("fail at courses")
                
            studentCourses = list(cursor)
            
            sql = "select project.projectid,project_name, filename from project left outer join file on (file.projectid = project.projectid) where userid = " + str(whileyid)
            print sql
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print err
                print("fail at projects")
                
            # Handle the pain of databases returning objects twice. 
            studentProjects = []
            projectFiles = {}
            for (projectid, projectname, filename) in cursor:
                if projectid not in projectFiles:
                    files = projectFiles[projectid] = []
                    studentProjects.append((projectid, projectname, files))
                if filename:
                    projectFiles[projectid].append(filename) 
            cursor.close()
            cnx.close()
        
        return templating.render("admin_students_search.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error,
                                REDIRECT=redirect, STATUS=status,
                                SEARCHRESULT=searchResult, SEARCHVALUE=searchValue,
                                STUDENTNAME=studentName, INSTITUTIONNAME=institutionName,
                                STUDENTCOURSES=studentCourses, STUDENTPROJECTS=studentProjects)

    admin_students_search.exposed = True


    # ============================================================
    # Admin Students  List page
    # ============================================================

    def admin_students_list(self, id=None, institution="", course=None, *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        options = []
        optionsCourse = []
        optionsStudent = []
        studentName = "No student selected"
        studentInstitution = ""
        studentCourses = ""
        studentProjects = ""
        whileyid = ""

        if id:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            sql = "select student_info_id,surname,givenname,institution_name,userid from student_info a,institution b where student_info_id = " + str(id) + " and a.institutionid = b.institutionid"
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print("Error Student id = " + id)
                
            _, surname, givenname, institution_name, userid = cursor.fetchone()
            studentName = fullname(givenname, surname)
            whileyid = str(userid)
            
            sql = "select c.course_name,c.code,year,c.courseid from student_course_link a left outer join course_stream b on a.coursestreamid = b.coursestreamid left outer join course c on b.courseid = c.courseid where a.studentinfoid = " + str(id)
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print("fail at courses")
                
            studentCourses = list(cursor)
            
            sql = "select project.projectid,project_name, filename from project left outer join file on (file.projectid = project.projectid) where userid = " + str(whileyid)
            print sql
            try:
                cursor.execute(sql)
            except db.DBError as err:
                print err
                print("fail at projects")
                
            # Handle the pain of databases returning objects twice. 
            studentProjects = []
            projectFiles = {}
            for (projectid, projectname, filename) in cursor:
                if projectid not in projectFiles:
                    files = projectFiles[projectid] = []
                    studentProjects.append((projectid, projectname, files))
                if filename:
                    projectFiles[projectid].append(filename) 
            cursor.close()
            cnx.close()
                    
        if institution:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query) 
            options = list(cursor)
            cursor.close()
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT institutionid,institution_name from institution order by institution_name")
            cursor.execute(query)
            for (institutionid,institution_name) in cursor:
                options.append((institutionid, institution_name))
                if institution == "":
                    institution = str(institutionid)
            cursor.close() 

        if course:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            sql = "SELECT courseid,code from course where institutionid = %s"
            cursor.execute(sql, institution)
            optionsCourse = list(cursor)
            cursor.close()   
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            sql = "SELECT courseid,code from course where institutionid = %s"
            cursor.execute(sql, institution)
            for (courseid,code) in cursor:
                optionsCourse.append((courseid, code))
                if course == "":
                    course = str(courseid)
            cursor.close()
        
        if course:
             cnx, status = db.connect()
             cursor = cnx.cursor() 
             sql = "SELECT distinct a.student_info_id,a.givenname,a.surname from student_info a,student_course_link b, course c, course_stream d where c.courseid = %s and  c.courseid = d.courseid and d.coursestreamid =b.coursestreamid and b.studentinfoid = a.student_info_id"
             cursor.execute(sql, (course,))
             for (student_info_id,givenname,surname) in cursor:
                 optionsStudent.append((student_info_id, name(givenname, surname)))
                 if course == "":
                    course = str(courseid)
             cursor.close()
              

        return templating.render("admin_students_list.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error,
                                REDIRECT=redirect, STATUS=status,
                                OPTION=options, INSTITUTION=institution, 
                                STUDENTNAME=studentName, STUDENTINSTITUTION=studentInstitution,
                                STUDENTCOURSES=studentCourses, STUDENTPROJECTS=studentProjects,
                                OPTIONCOURSE=optionsCourse, COURSE=course, OPTIONSTUDENT=optionsStudent)

    admin_students_list.exposed = True

def name(given, sur):
    return web.safe(sur) + ", " + web.safe(given)

def fullname(given, sur):
    return web.safe(given) + " " + web.safe(sur)
