import cgi
import cgitb; cgitb.enable()
import sys
import psycopg2
form = cgi.FieldStorage(keep_blank_values=1)

# Variables
institution = ""

# Database Connections
conn_string = "host='localhost' dbname='whileyideschema' user='postgres' password='lv426111'"
conn = psycopg2.connect(conn_string)

print
print("HTTP/1.0 200 OK\n")
print

print('<HTML><HEAD><TITLE>Whiley Admin (dev)</TITLE></HEAD>')

if form:
	if form['institution'].value:
		institution = form['institution'].value
		insert_cursor = conn.cursor()
		insert_cursor.execute("insert into institution (institution_name) values ('" + institution + "');")
	
print('<style>\n'
      'body { font-family:arial; }\n'
      '.dashboardMenu td {\n'
      'text-align:center;\n'
      'padding-right:40px;}\n')
print('a:link { text-decoration: none; color:#A58158; border-bottom:1px dotted;}')  
print('a:visited { text-decoration: none; color:#A58158; border-bottom:1px dotted; }')
print('a:hover { text-decoration:none;color:#D7CF88;border-bottom:1px dotted; }')

print('.content { padding-left:20px;border: 2px solid #000000;'
      'border-radius: 25px; margin-top:20px; background:#D5C397; height:50%}')
print('h2 {  padding-top:0px; padding-top:20px; margin:0px; }')

print('</style>')
print('<BODY>')
print('<H1>Dashboard line</H1>')
print('<table class=\"dashboardMenu\"><tr><td><img src=\"images/home.png\"></td><td><img src=\"images/institution.png\"></td><td><img src=\"images/course.png\"></td><td><img src=\"images/addcourse.png\"></td><td><img src=\"images/student.png\"></td></tr>'
      '</td><td><a href=\"index.py\">Home</a></td><td><a href=\"institution.py\">Institution</a></td><td><a href=\"#\">Courses</td><td><a href=\"#\">Add Course</td><td><a href=\"#\">Students</a></td></tr></table>')

print('<div class=\"content\"><br><table><tr><td width=\"55\" align=\"left\"><img src=\"images/institution_small.png\"></td><td><h2> Current Institutions</h2></td></tr>'
'<tr><td>&nbsp;</td><td><select>')
cursor = conn.cursor()
cursor.execute("SELECT * FROM institution order by institution_name")
for row in cursor:
	print('<option value="' + str(row[0]) +'">' + row[1] + '</option>')

#<option value="AUT">AUT</option><option value="MIT">MIT</option><option value="VUW">VUW</option>

print('</select></td></tr></table>')

print('<br><hr><table><tr><td width=\"55\" align=\"left\"><img src=\"images/institution_add_small.png\"></td><td><h2> Add New Institution</h2></td></tr>'
'<tr><td>&nbsp;</td><td><form method=\"post\" action=\"institution.py\"><table><tr><td> Institution Name </td><td> <input name="institution" type="textfield" size="50"></td></tr></table><br><input type=\"submit\" value=\"Add\"></form></td></tr></table></div>')

print('</BODY>')
