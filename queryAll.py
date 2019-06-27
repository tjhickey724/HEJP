#!/usr/bin/python
import psycopg2
import timeit

def generateIndices():
    queryAll("Create index year_idx on hej(year)")
    queryAll("create index faculty_idx on hej(faculty)")

def demo(n):
    switcher = {
    1: "SELECT year,faculty, count(*) as N from hej group by year,faculty;",
    2: "SELECT fulltimecontingent, count(*) from hej where year =2010 group by  fulltimecontingent",
    3: "SELECT parttimecontingent, count(*) from hej where year =2010 group by  parttimecontingent",
    4: "SELECT year,count(*) from hej where (tenured=1 or tenure_track=1) group by year;",
    }
    z = queryAll(switcher.get(n,0))
    for row in z:
        print(row)
    return z

def queryAll(query):
    """ Connect to the PostgreSQL database server """
    conn = None
    result = None
    try:
        # read connection parameters
        conn_string = "host='localhost' dbname='HEJP' user='postgres' password='a12s34d56'"


        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(conn_string)

        # create a cursor
        cur = conn.cursor()

 # execute a statement
        cur.execute(query)

        # display the PostgreSQL database server version
        result = cur.fetchall()
        print(result)

     # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
        return result
