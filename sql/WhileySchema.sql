
CREATE TABLE whiley_user(userid INTEGER AUTO_INCREMENT , username  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , password  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , email_address  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin ,PRIMARY KEY (userid));
CREATE TABLE project(
projectid INTEGER AUTO_INCREMENT , 
project_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
userid INTEGER
,PRIMARY KEY (projectid)
)
;
CREATE TABLE file(
fileid INTEGER AUTO_INCREMENT , 
projectid INTEGER, 
filename  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
source  LONGBLOB 
,PRIMARY KEY (fileid)
)
;
CREATE TABLE student_info(
student_info_id INTEGER AUTO_INCREMENT , 
identifier  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
login  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
givenname  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
surname  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin ,
preferred_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
userid INTEGER, 
institutionid INTEGER
,PRIMARY KEY (student_info_id)
)
;
CREATE TABLE student_course_link(
studentinfoid INTEGER, 
coursestreamid INTEGER)
;
CREATE TABLE teacher_info(
teacherid INTEGER AUTO_INCREMENT , 
staffid  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
login  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
full_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
preferred_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
userid INTEGER
,PRIMARY KEY (teacherid)
)
;
CREATE TABLE teacher_course_link(
teacherinfoid INTEGER, 
courseid INTEGER)
;
CREATE TABLE course(
courseid INTEGER AUTO_INCREMENT , 
course_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
code  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
year INTEGER, 
institutionid INTEGER
,PRIMARY KEY (courseid)
)
;
CREATE TABLE course_stream(
coursestreamid INTEGER AUTO_INCREMENT , 
stream_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
courseid INTEGER
,PRIMARY KEY (coursestreamid)
)
;
CREATE TABLE institution(
institutionid INTEGER AUTO_INCREMENT , 
institution_name  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
contact  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
website  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin , 
description  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin 
,PRIMARY KEY (institutionid)
)
;
CREATE TABLE schema_version(
versionnumber  VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_bin )
;
CREATE TABLE assignment(
assignmentid INTEGER AUTO_INCREMENT , 
coursestreamid INTEGER, 
duedate  DATETIME 
,PRIMARY KEY (assignmentid)
)
;