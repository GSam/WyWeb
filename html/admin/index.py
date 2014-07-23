print
print("HTTP/1.0 200 OK\n")
print

print('<HTML><HEAD><TITLE>Whiley Admin (dev)</TITLE></HEAD>')

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
print('h2 {  padding-top:20px; }')

print('</style>')
print('<BODY>')
print('<H1>Dashboard line</H1>')
print('<table class=\"dashboardMenu\"><tr><td><img src=\"images/home.png\"></td><td><img src=\"images/institution.png\"></td><td><img src=\"images/course.png\"></td><td><img src=\"images/addcourse.png\"></td><td><img src=\"images/student.png\"></td></tr>'
      '</td><td><a href=\"index.py\">Home</a></td><td><a href=\"institution.py\">Institution</a></td><td><a href=\"#\">Courses</td><td><a href=\"#\">Add Course</td><td><a href=\"#\">Students</a></td></tr></table>')

print('<div class=\"content\"><h2>Current Status</h2>'
'</div>')
print('</BODY>')
