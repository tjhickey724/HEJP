from __future__ import division
import os
from flask import Flask
from flask import Markup
from flask import redirect
from flask import Blueprint,render_template, abort
from flask import request
from jinja2 import TemplateNotFound
import psycopg2
import timeit
from collections import OrderedDict
from query import *
from fieldValues import *
from occupations import occupations
from nsfFields import *
from parse import *
from skillField import *
import pandas as pd
import numpy as np
from collections import Counter
from calculate import *

project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')


@app.route('/',methods=["GET"])
def home():
    return render_template("homemini.html")

@app.route('/test',methods=["GET"])
def test():
    result = queryAll("Select * from maintable limit 5")
    return render_template("test.html",result=result)

@app.route('/about',methods=["GET"])
def about():
    return render_template("about.html")

def queryAll(query):
    """ Connect to the PostgreSQL database server """
    conn = None
    result = None
    try:
        # read connection parameters
        # conn_string = "host='localhost' dbname='HEJP' user='postgres' password='a12s34d56'"
        conn_string = "dbname='hejp' user='tim' password='none'"
        #conn_string = "dbname='hejp' user='tim' password='HeJp19-20zz!!**'"


        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(conn_string)

        # create a cursor
        cur = conn.cursor()

 # execute a statement
        cur.execute(query)

        # display the PostgreSQL database server version
        result = cur.fetchall()
        # print(result)

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
    # app.run(debug=True)
    app.run(host="turing.cs-i.brandeis.edu",port=7000,debug=False)
