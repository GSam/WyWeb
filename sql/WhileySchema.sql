
 DROP TABLE whiley_user;
 DROP TABLE project;
 DROP TABLE file;
 DROP TABLE student_info;
 DROP TABLE student_course_link;
 DROP TABLE teacher_info;
 DROP TABLE course;
 DROP TABLE institution;
 DROP TABLE schema_version;
 CREATE TABLE whiley_user(
userid  SERIAL , 
username VARCHAR(1000), 
password VARCHAR(1000), 
email_address VARCHAR(1000)
,PRIMARY KEY (userid)
)
;
 CREATE TABLE project(
projectid  SERIAL , 
project_name VARCHAR(1000), 
userid INTEGER
,PRIMARY KEY (projectid)
)
;
 CREATE TABLE file(
fileid  SERIAL , 
projectid INTEGER, 
filename VARCHAR(1000), 
source  BYTEA 
,PRIMARY KEY (fileid)
)
;
 CREATE TABLE student_info(
student_info_id  SERIAL , 
identifier VARCHAR(1000), 
login VARCHAR(1000), 
fullname VARCHAR(1000), 
preferred_name VARCHAR(1000), 
userid INTEGER
,PRIMARY KEY (student_info_id)
)
;
 CREATE TABLE student_course_link(
studentinfoid INTEGER, 
coursestreamid INTEGER)
;
 CREATE TABLE teacher_info(
teacherid  SERIAL , 
staffid VARCHAR(1000), 
login VARCHAR(1000), 
full_name VARCHAR(1000), 
preferred_name VARCHAR(1000), 
userid INTEGER
,PRIMARY KEY (teacherid)
)
;
 CREATE TABLE course(
courseid  SERIAL , 
course_name VARCHAR(1000), 
code VARCHAR(1000), 
year INTEGER, 
institutionid INTEGER
,PRIMARY KEY (courseid)
)
;
 CREATE TABLE institution(
institutionid  SERIAL , 
institution_name VARCHAR(1000)
,PRIMARY KEY (institutionid)
)
;
 CREATE TABLE schema_version(
versionnumber VARCHAR(1000))
;