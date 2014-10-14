import cherrypy, config, web
import templating, db
from cherrypy.lib.cptools import allow
from cherrypy import request
import auth
from auth import AuthController, requireAdmin, requireAdminOrTeacher, isAdmin

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
        requireAdminOrTeacher(userid)
        
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        status = "DB: Connection ok"
        cnx = db.connect()

        return templating.render("admin.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, REDIRECT=redirect,
                                STATUS=status, IS_ADMIN=isAdmin(userid))
    admin.exposed = True

    # ============================================================
    # Manage admin page
    # ============================================================
    def manage_admins(self, newadminid="", deleteadminid="", searchuser=None, newteacherid="", *args, **kwargs):
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
        adminUserid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(adminUserid)

        allow(["HEAD", "GET", "POST"])
        message = ""
        redirect = "NO"
        adminList = []
        userList = []

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

        teacherList = []
        teacherMessage = ""

        if newteacherid == "":          
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            query = ("SELECT full_name, userid from teacher_info")
            cursor.execute(query)
            for (username, userid) in cursor:
                teacherList.append((username,userid))
            cursor.close()
            userid = None

        return templating.render("manage_admins.html", ADMINLIST=adminList, TEACHERLIST=teacherList, 
                                    MESSAGE=message, TEACHER_MESSAGE=teacherMessage, IS_ADMIN=isAdmin(adminUserid))

    manage_admins.exposed = True

    def admin_manage_revoke(self, id):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        if request.method == 'POST':
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "DELETE FROM admin_users WHERE userid=%s"
            cursor.execute(query, (id,))
            cursor.close()
            cnx.close()

            return templating.render("redirect.html", STATUS="alert-success", 
                                    MESSAGE="Admin rights revoked...")
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "SELECT username FROM whiley_user WHERE userid=%s"
            cursor.execute(query, (id,))
            name = cursor.fetchone()[0]
            cursor.close()
            cnx.close()

            return templating.render("confirm.html", 
                                TITLE="Are you sure you want to revoke %s's admin rights?" % name,
                                MESSAGE="", CONFIRM_LABLE="REVOKE")
    admin_manage_revoke.exposed = True

    def admin_teacher_add(self, id, login="", staffid="", full_name="", preferred_name="", *args, **kwargs):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        if request.method == 'POST' and login and staffid and full_name and preferred_name:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "SELECT userid FROM whiley_user WHERE username = %s"
            cursor.execute(query, (id,))
            id = cursor.fetchone()[0]
            cursor.close()
            cnx.close()

            auth.create_teacher(id, login, staffid, full_name, preferred_name)

            return templating.render("redirect.html", STATUS="alert-success", MESSAGE="Teacher rights added...")
        else:
            # prefill login
            if not login:
                login = id

            return templating.render("admin_add_teacher.html", USERID=id, LOGIN=login, STAFFID=staffid,
                                        FULLNAME=full_name, PREFERRED_NAME=preferred_name, 
                                        IS_ADMIN=isAdmin(userid))
    admin_teacher_add.exposed = True

    def admin_teacher_revoke(self, id):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        if request.method == 'POST':
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "DELETE FROM teacher_info WHERE userid=%s"
            cursor.execute(query, (id,))
            cursor.close()
            cnx.close()

            return templating.render("redirect.html", STATUS="alert-success", 
                                    MESSAGE="Admin rights revoked...")
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "SELECT username FROM whiley_user WHERE userid=%s"
            cursor.execute(query, (id,))
            name = cursor.fetchone()[0]
            cursor.close()
            cnx.close()

            return templating.render("confirm.html", 
                                TITLE="Are you sure you want to revoke %s's teaching rights?" % name,
                                MESSAGE="", CONFIRM_LABLE="REVOKE")
    admin_teacher_revoke.exposed = True

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

        return templating.render("admin_institutions_add.html", ROOT_URL=config.VIRTUAL_URL, ERROR="",
                                REDIRECT="", OPTION=options, STATUS=status, IS_ADMIN=isAdmin(userid))

    admin_institutions_add.exposed = True

    def admin_institutions_remove(self, id):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        if request.method == 'POST':
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "DELETE FROM institution WHERE institutionid=%s"
            cursor.execute(query, (id,))
            query = "DELETE FROM course where institutionid = %s"
            cursor.execute(query, (id,))
            cursor.close()
            cnx.close()

            return templating.render("redirect.html", STATUS="alert-success", 
                                    MESSAGE="Institution deleted...")
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "SELECT institution_name FROM institution WHERE institutionid=%s"
            cursor.execute(query, (id,))
            name = cursor.fetchone()[0]
            cursor.close()
            cnx.close()

            return templating.render("confirm.html", TITLE="Are you sure you want to delete "+name+"?",
                                MESSAGE="The institution and all it's courses will be permanently removed.",
                                CONFIRM_LABLE="DELETE")
    admin_institutions_remove.exposed = True

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
                               DESCRIPTION=displayDescription, IS_ADMIN=isAdmin(userid))

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
                                COURSE_LIST=course_list, IS_ADMIN=isAdmin(userid))

    admin_courses.exposed = True
    
    
        # ============================================================ 
        # Admin Add Course page 
        # ============================================================ 
    
     
    def admin_course_add(self, course_name=None, course_code=None, course_year=None, 
                        course_institution=None, validation_code=None, *args, **kwargs): 
        """
        Adds a course to the database. 
        """
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

        return templating.render("admin_courses_add.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error,
                                    REDIRECT=redirect, OPTION=options, NEWSTATUS=newstatus, 
                                    VALIDATIONCODE=validationCode, IS_ADMIN=isAdmin(userid))  
                               
    admin_course_add.exposed = True
    
    def admin_course_remove(self, id):
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        if request.method == 'POST':
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = "DELETE FROM course WHERE courseid=%s"
            cursor.execute(query, (id,))
            cursor.close()
            cnx.close()

            return templating.render("redirect.html", STATUS="alert-success", 
                                    MESSAGE="Course deleted...")
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor()
            query = """SELECT course.course_name, institution.institution_name FROM course, institution 
                    WHERE course.courseid=%s AND institution.institutionid = course.institutionid"""
            cursor.execute(query, (id,))
            course, institution = cursor.fetchone()
            cursor.close()
            cnx.close()

            return templating.render("confirm.html",
                            TITLE="Are you sure you want to delete %s at %s?" % (course, institution),
                            MESSAGE="This course will be permanently removed.", CONFIRM_LABLE="DELETE")
    admin_course_remove.exposed = True

    # ============================================================
    # Admin Course details page
    # ============================================================

    def admin_course_details(self, id, *args, **kwargs):
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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdmin(userid)

        allow(["HEAD", "GET", "POST"])
        error = ""
        redirect = "NO"
        newstatus = "" 
        students = []
        courseId = id

        cnx, status = db.connect()
        cursor = cnx.cursor() 
       
        query = ("SELECT courseid,course_name,code,year,validationcode,institution_name from course a, institution b where a.institutionid = b.institutionid and a.courseid = %s")
        cursor.execute(query, (id,))
        courseID, courseName, courseCode, year, validationcode, institution = cursor.fetchone()

        sql = "SELECT distinct a.student_info_id,a.givenname,a.surname from student_info a,student_course_link b, course c, course_stream d where c.courseid = %s and  c.courseid = d.courseid and d.coursestreamid =b.coursestreamid and b.studentinfoid = a.student_info_id order by a.surname"

        cursor.execute(sql, (str(courseID),))
        students = [(id, name(givenname, surname)) for id, givenname, surname in cursor]

        sql = """SELECT distinct a.teacherid,a.full_name 
                from teacher_info a, teacher_course_link b
                where b.courseid = %s and b.teacherinfoid = a.teacherid"""
        cursor.execute(sql, (str(courseID),))
        teachers = list(cursor)

        sql = """SELECT stream_name from course_stream where courseid = %s"""
        cursor.execute(sql, (str(courseId),))
        streams = [ret[0] for ret in cursor]

        cursor.close()
        
        return templating.render("admin_course_details.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error, 
            REDIRECT=redirect, TEACHERS=teachers, STREAMS=streams, 
            COURSENAME=courseName, COURSECODE=courseCode, YEAR=year, VALIDATIONCODE=validationcode,
            INSTITUTION=institution, STUDENTS=students, COURSEID=courseId, IS_ADMIN=isAdmin(userid))
    admin_course_details.exposed = True
    

    def admin_course_add_teacher(self, courseid, username, *args, **kwargs):
        """Adds a teacher to a course."""
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdminOrTeacher(userid)

        allow(['POST'])

        cnx, status = db.connect()
        cursor = cnx.cursor()

        query = """SELECT t.teacherid FROM teacher_info t, whiley_user u 
                    WHERE u.username = %s AND u.userid = t.userid"""
        cursor.execute(query, (username,))
        teacherid = cursor.fetchone()
        if not teacherid:
            return templating.render("redirect.html", STATUS="alert-warning", MESSAGE="No such teacher!")
        teacherid = teacherid[0]

        query = """INSERT INTO teacher_course_link (teacherinfoid, courseid) VALUES (%s, %s)"""
        cursor.execute(query, (teacherid, courseid))
        if not cursor.rowcount:
            return templating.render("redirect.html", STATUS="alert-warning", MESSAGE="Failed to add teacher!")
        return templating.render("redirect.html", STATUS="alert-success", MESSAGE="Teacher added.")
    admin_course_add_teacher.exposed=True

    def admin_course_add_stream(self, courseid, name, *args, **kwargs):
        """Adds a stream to a course."""
        userid = cherrypy.session.get(auth.SESSION_USERID)
        requireAdminOrTeacher(userid)

        allow(['POST'])
        print courseid, name

        cnx, status = db.connect()
        cursor = cnx.cursor()

        query = """INSERT INTO course_stream (stream_name, courseid) VALUES (%s, %s)"""
        cursor.execute(query, (name, courseid))
        if not cursor.rowcount:
            return templating.render("redirect.html", STATUS="alert-warning", MESSAGE="Failed to add course stream!")
        return templating.render("redirect.html", STATUS="alert-success", MESSAGE="Course stream added.")
    admin_course_add_stream.exposed=True

    # ============================================================
    # Admin Students search page
    # ============================================================

    def admin_students_search(self, searchValue="", id=None, *args, **kwargs):
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
        isAdmin, _, permittedStudents = getAccessPermissions()

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
                            for id_, surname, givenname in cursor 
                            if permittedStudents is None or id_ in permittedStudents]
            cursor.close()
            cnx.close()

        status, studentName, institutionName, studentCourses, studentProjects = \
                studentInfo(id)
        
        return templating.render("admin_students_search.html", ROOT_URL=config.VIRTUAL_URL, ERROR=error,
                                REDIRECT=redirect, STATUS=status,
                                SEARCHRESULT=searchResult, SEARCHVALUE=searchValue,
                                STUDENTNAME=studentName, INSTITUTIONNAME=institutionName,
                                STUDENTCOURSES=studentCourses, STUDENTPROJECTS=studentProjects, 
                                IS_ADMIN=isAdmin)

    admin_students_search.exposed = True


    # ============================================================
    # Admin Students  List page
    # ============================================================

    def admin_students_list(self, id=None, institution="", course=None, *args, **kwargs):
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
        userid = cherrypy.session.get(auth.SESSION_USERID)
        isAdmin, permittedCourses, permittedStudents = True, None, None # Quick reverse on nonfunctioning getAccessPermissions()
        requireAdmin(userid)

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
            optionsCourse = [(courseid, code) for courseid, code in cursor 
                                if permittedCourses is None or courseid in permittedCourses]
            cursor.close()   
        else:
            cnx, status = db.connect()
            cursor = cnx.cursor() 
            sql = "SELECT courseid,code from course where institutionid = %s"
            cursor.execute(sql, institution)
            for (courseid,code) in cursor:
                if permittedCourses is None or courseid in permittedCourses:
                    optionsCourse.append((courseid, code))
                    if course == "":
                        course = str(courseid)
            cursor.close()
        
        if course and (permittedCourses is None or course in permittedCourses):
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
                                OPTIONCOURSE=optionsCourse, COURSE=course, OPTIONSTUDENT=optionsStudent, 
                                IS_ADMIN=isAdmin)

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

def getAccessPermissions():
    userid = cherrypy.session.get(auth.SESSION_USERID)
    if auth.isAdmin(userid):
        return True, None, None
    elif auth.isTeacher(userid):
        cnx, status = db.connect()
        cursor = cnx.cursor()
        sql = """select tc.courseid from teacher_course_link tc, teacher_info t 
                where tc.teacherinfoid = t.teacherid and t.userid = %s"""
        cursor.execute(sql, (userid,))
        courses = [ret[0] for ret in cursor.fetchall()]

        sql = """select sc.studentinfoid 
                from teacher_info t, teacher_course_link tc, course_stream cs, student_course_link sc
                where t.userid = %s and tc.teacherinfoid = t.teacherid and tc.courseid = cs.courseid 
                    and cs.coursestreamid = sc.coursestreamid"""
        cursor.execute(sql, (userid,))
        students = [ret[0] for ret in cursor.fetchall()]
        return False, courses, students
    else:
        raise cherrypy.HTTPRedirect("/auth/login")
