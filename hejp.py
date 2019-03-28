import os

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
import psycopg2
import timeit


project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')



query1 = "SELECT year,faculty, count(*) as N from hej where faculty=1 group by faculty,year;"

@app.route('/',methods=["GET"])
def home():
    return render_template("home.html")


@app.route('/demo1', methods=["GET", "POST"])
def demo1():
    z = demo(1)
    return render_template("demo1.html", query=query1, rows=z)

@app.route('/demo2', methods=["GET", "POST"])
def demo2():
    z = demo(1)
    results = [[x[0],x[1],x[2]] for x in z]
    return render_template("demo2.html", query=query1, rows=results)




def demo(n):
    switcher = {
    1: "SELECT year,faculty, count(*) as N from hej where faculty=1 group by faculty,year;",
    2: "SELECT fulltimecontingent, count(*) from hej where year =2010 group by  fulltimecontingent",
    3: "SELECT parttimecontingent, count(*) from hej where year =2010 group by  parttimecontingent",
    4: "SELECT year,count(*) from hej where (tenured=1 or tenure_track=1) group by year;",
    }
    z = queryAll(switcher.get(n,0))
    return z

def queryAll(query):
    """ Connect to the PostgreSQL database server """
    conn = None
    result = None
    try:
        # read connection parameters
        conn_string = "host='localhost' dbname='data1000' user='postgres' password='postgres'"


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


if __name__ == "__main__":
    app.run(debug=True)
