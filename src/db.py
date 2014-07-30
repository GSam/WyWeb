import cherrypy

import mysql.connector

#cnx = cursor = None
def connect(): 
	#global cnx
	#global cursor
	cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley') 

	return cnx


