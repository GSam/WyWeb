import cherrypy

import mysql.connector
from mysql.connector import errorcode

#connection details
def connect():
    try:
        status = "OK"
        cnx = connect_dev()
        #mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            status = "Something is wrong with your user name or password"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            status = "Database does not exists"
        else:
            status = err
    return cnx, status


def connect_old():
    return mysql.connector.connect(host="kipp-cafe.ecs.vuw.ac.nz", user="whiley", database="whiley", passwd="coyote")

def connect_dev():
    return mysql.connector.connect(host="depot.ecs.vuw.ac.nz", user="whiley", database="whileydev_s302_2014", passwd="coyote2Dev")

def connect_prod():
    return mysql.connector.connect(host="depot.ecs.vuw.ac.nz", user="whiley", database="whiley_s302_2014", passwd="coyote2Dev")
