import cherrypy

import mysql.connector

#connection details
def connect(): 
    try:
        cnx = mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            status = "Something is wrong with your user name or password"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            status = "Database does not exists"
        else:
            status = err
    return cnx


