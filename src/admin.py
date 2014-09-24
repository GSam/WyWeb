import cherrypy, config, web
import templating, db
from cherrypy.lib.cptools import allow
import auth
from auth import AuthController, requireAdmin

def authorizeTests():
    global requireAdmin
    cherrypy.session = {}
    def innerRequireAdmin(_):
        return True
    requireAdmin = innerRequireAdmin

class Admin(object):
    """Contains methods associated with the admin. 

    If any tests in this class fails, check the database first.

    Test that it can be instantiated, methods tested seperately.
    >>> self = Admin()
    """
    # ============================================================
    # Admin Main Page
    # ============================================================
    def admin(self, *args, **kwargs):
        """
        The admin homepage should return a template for the admin page.

        >>> authorizeTests()
        >>> self = Admin()
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

    def admin_institutions_remove(self, id):
        username = cherrypy.session.get("_cp_username")
        requireAdmin(username)

        allow(["POST"])

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = "DELETE FROM institution WHERE institutionid=%s"
        cursor.execute(query, (id,))
        cursor.close()
        cnx.close()

        return templating.render("redirect.html", STATUS="alert-success", 
                                MESSAGE="Institution deleted...")
    admin_institution_remove.exposed = True

    # ============================================================
    # Admin Institutions Page
    # ============================================================

    def admin_institutions(self, institution="", *args, **kwargs):
        """
        Lists available institutions.

        >>> authorizeTests()
        >>> self = Admin()
        >>> ret = self.admin_institutions()
        >>> ('Victoria University of Wellington', 2) in ret.OPTION
        True
        >>> ret = self.admin_institutions(2)
        >>> ret.INSTITUTION_ID, ret.INSTITUTION, ret.CONTACT, ret.WEBSITE, ret.DESCRIPTION
        (2, 'Victoria University of Wellington', None, None, None)
        """
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
        """
        Lists all available courses. 

        >>> authorizeTests()
        >>> self = Admin()
        >>> ret = self.admin_courses()
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> ret = self.admin_courses('2')
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> ret.INSTITUTION
        '2'
        >>> (1, 'SWEN302') in ret.COURSE_LIST
        True
        """
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
        """
        Adds a course to the database. 
        """

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
    
    def admin_course_remove(self, id):
        username = cherrypy.session.get("_cp_username")
        requireAdmin(username)

        allow(["POST"])

        cnx, status = db.connect()
        cursor = cnx.cursor()
        query = "DELETE FROM course WHERE courseid=%s"
        cursor.execute(query, (id,))
        cursor.close()
        cnx.close()

        return templating.render("redirect.html", STATUS="alert-success", 
                                MESSAGE="Course deleted...")
    admin_course_remove.exposed = True

    # ============================================================
    # Admin Course details page
    # ============================================================

    def admin_course_details(self, id, *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)
        """
        Retrieves course details.

        >>> authorizeTests()
        >>> self = Admin()
        >>> ret = self.admin_course_details('1')
        >>> ret.COURSENAME, ret.COURSECODE, ret.YEAR
        ('Agile Methods', 'SWEN302', 2014)
        >>> ret.VALIDATIONCODE, ret.INSTITUTION
        (u'aaaa', 'Victoria University of Wellington')
        >>> 'dave, dave' in ret.STUDENTS
        True
        """

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
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
            REDIRECT=redirect,
            COURSENAME=courseName, COURSECODE=courseCode, YEAR=year, VALIDATIONCODE=validationcode,
            INSTITUTION=institution, STUDENTS=students)
    admin_course_details.exposed = True
    

    # ============================================================
    # Admin Students search page
    # ============================================================

    def admin_students_search(self, searchValue="", id=None, *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)
        """
        Searches students by searchValue, displaying information for student number id. 

        >>> authorizeTests()
        >>> self = Admin()
        >>> ret = self.admin_students_search()
        >>> ret.SEARCHRESULT, ret.SEARCHVALUE
        ([], '')
        >>> ret.STUDENTNAME, ret.INSTITUTIONNAME, ret.STUDENTCOURSES, ret.STUDENTPROJECTS
        ('', '', [], [])

        >>> ret = self.admin_students_search("dav")
        >>> ret.SEARCHVALUE
        'dav'
        >>> (70, 'dave, dave') in ret.SEARCHRESULT
        True
        >>> ret.STUDENTNAME, ret.INSTITUTIONNAME, ret.STUDENTCOURSES, ret.STUDENTPROJECTS
        ('', '', [], [])

        >>> ret = self.admin_students_search("dav", 70)
        >>> ret.SEARCHVALUE
        'dav'
        >>> (70, 'dave, dave') in ret.SEARCHRESULT
        True
        >>> ret.STUDENTNAME, ret.INSTITUTIONNAME
        ('dave dave', 'Victoria University of Wellington')
        >>> ('Agile Methods', 'SWEN302', 2014, 1) in ret.STUDENTCOURSES
        True
        """

        allow(["HEAD", "GET", "POST"])
        error = ""
        searchResult = []
        redirect = "NO"
        status = "DB: Connection ok"
        studentCourses = []
        studentProjects = []

        if searchValue:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            join = '%' + searchValue.upper() + '%'
            sql = "select student_info_id,surname,givenname from student_info where UPPER(givenname) like %s or UPPER(surname) like %s order by surname"
            cursor.execute(sql, (join,join))
            searchResult = [(id_, name(givenname, surname)) 
                            for id_, surname, givenname in cursor]
            cursor.close()
            cnx.close()

        status, studentName, institutionName, studentCourses, studentProjects = \
                studentInfo(id)
        
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
        """
        Lists students under a institution and course. 

        >>> authorizeTests()
        >>> self = Admin().admin_students_list
        >>> ret = self()
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> ret.STUDENTNAME, ret.STUDENTCOURSES
        ('No student selected', [])

        >>> ret = self(institution='2')
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> (1, 'SWEN302') in ret.OPTIONCOURSE
        True
        >>> ret.INSTITUTION
        '2'
        >>> ret.STUDENTNAME, ret.STUDENTCOURSES
        ('No student selected', [])

        >>> ret = self(institution='2', course='1')
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> ret.INSTITUTION
        '2'
        >>> (1, 'SWEN302') in ret.OPTIONCOURSE
        True
        >>> ret.COURSE
        '1'
        >>> (70, 'dave, dave') in ret.OPTIONSTUDENT
        True
        >>> ret.STUDENTNAME, ret.STUDENTCOURSES
        ('No student selected', [])
        
        >>> ret = self(70, '2', '1')
        >>> (2, 'Victoria University of Wellington') in ret.OPTION
        True
        >>> ret.INSTITUTION
        '2'
        >>> (1, 'SWEN302') in ret.OPTIONCOURSE
        True
        >>> ret.COURSE
        '1'
        >>> (70, 'dave, dave') in ret.OPTIONSTUDENT
        True
        >>> ret.STUDENTNAME
        'dave dave'
        >>> ('Agile Methods', 'SWEN302', 2014, 1) in ret.STUDENTCOURSES
        True
        """

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        options = []
        optionsCourse = []
        optionsStudent = []
        studentInstitution = ""

        status, studentName, studentInstitution, studentCourses, studentProjects = \
                studentInfo(id, "No student selected")

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
    """
    Formats a name in a websafe "lastname, firstname" format.

    >>> name("david", "pearce")
    'pearce, david'
    >>> name("<em>attacker</em>", "nefarious<script>alert('BOO!')</script>")
    "nefarious&lt;script&gt;alert('BOO!')&lt;/script&gt;, &lt;em&gt;attacker&lt;/em&gt;"
    """
    return web.safe(sur) + ", " + web.safe(given)

def fullname(given, sur):
    """
    Formats a name in a websafe "firstname lastname" format.

    >>> fullname("david", "pearce")
    'david pearce'
    >>> fullname("<em>attacker</em>", "nefarious<script>alert('BOO!')</script>")
    "&lt;em&gt;attacker&lt;/em&gt; nefarious&lt;script&gt;alert('BOO!')&lt;/script&gt;"
    """
    return web.safe(given) + " " + web.safe(sur)

def studentInfo(id, defaultName=""):
    status = "DB: Connection ok"
    studentName = defaultName
    institution_name = ""
    whileyid = None
    studentCourses = studentProjects = []

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

    return status, studentName, institution_name, studentCourses, studentProjects
