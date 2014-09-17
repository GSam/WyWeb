import cherrypy

import mysql.connector
from mysql.connector import errorcode

import db_config

DBError = mysql.connector.Error

# connection details
def connect():
    """Return the connection.
    >>> connect()[1]
    'OK'
    """
    cnx = False
    try:
        status = "OK"
        cnx = connect_from_config()
        check_schema(cnx)
        #mysql.connector.connect(user='whiley', password='coyote',host='kipp-cafe.ecs.vuw.ac.nz',database='whiley')
    except DBError as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            status = "Something is wrong with your user name or password"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            status = "Database does not exists"
        else:
            status = err
    return cnx, status


def connect_from_config():
##    print db_config.HOST
##    print db_config.DATABASE
##    print db_config.USER
    #     print db_config.PASSWORD
    return mysql.connector.connect(
        host=db_config.HOST,
        database=db_config.DATABASE,
        port=3306,
        user=db_config.USER,
        passwd=db_config.PASSWORD)


def connect_old():
    return mysql.connector.connect(host="kipp-cafe.ecs.vuw.ac.nz", user="whiley", database="whiley", passwd="coyote")


def connect_dev():
    return mysql.connector.connect(host="depot.ecs.vuw.ac.nz", user="whiley", database="whileydev_s302_2014",
                                   passwd="coyote2Dev")


def connect_prod():
    return mysql.connector.connect(host="depot.ecs.vuw.ac.nz", user="whiley", database="whiley_s302_2014",
                                   passwd="coyote2Dev")


def test_db():

    cnx = connect()[0]
    cursor = cnx.cursor()
    query = ("SELECT username from whiley_user")
    cursor.execute(query)
    for (username) in cursor:
        print("{} name".format(username))
    cursor.close()
    cnx.close()



def check_schema(cnx):
##    print "Creating Schema"
    try:
        FOUND_USERS = False
        try:
            cursor = cnx.cursor()
            cursor.execute("SELECT * from whiley_user;")
            for (whiley_user) in cursor:
                FOUND_USERS = True
        except DBError as err:
            print err
        if (not FOUND_USERS):
            with open('sql/DropSchema.sql', 'r') as script_file:
                drop_schema_script = script_file.read()
                print drop_schema_script
                cursor = cnx.cursor()
                for result in cursor.execute(drop_schema_script, params=None, multi=True):
                    if result.with_rows:
                        print("Rows produced by statement '{}':".format(result.statement))
                        print(result.fetchall())
                    else:
                        print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))
                cursor.execute("commit;")

            with open('sql/WhileySchema.sql', 'r') as script_file:
                create_schema_script = script_file.read()
                print create_schema_script
                cursor = cnx.cursor()
                for result in cursor.execute(create_schema_script, params=None, multi=True):
                    if result.with_rows:
                        print("Rows produced by statement '{}':".format(result.statement))
                        print(result.fetchall())
                    else:
                        print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))
                cursor.execute("commit;")
            with open('sql/DummyData.sql', 'r') as dummy_data_file:
                dummy_data_script = dummy_data_file.read()
                print dummy_data_script
                cursor = cnx.cursor()
                for result in cursor.execute(dummy_data_script, params=None, multi=True):
                    if result.with_rows:
                        print("Rows produced by statement '{}':".format(result.statement))
                        print(result.fetchall())
                    else:
                        print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))
                cursor.execute("commit;")
        cursor.close
    except DBError as err:
        print err

