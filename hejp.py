import os
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
import psycopg2
import timeit

from occupations import occupations

project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')

faculty_status ="""
tenured
tenured_track
fulltimecontingent
parttimecontingent""".split("\n")


fields_of_study ="""fs_life_sciences
fs_physical_sciences_and_earth_s
fs_mathematics_and_computer_scie
fs_psychology_and_social_science
fs_engineering
fs_education
fs_humanities_and_arts
fs_others""".split("\n")

departments ="""agriculturalsciencesandnaturalre
biologicalandbiomedicalsciences
healthsciences
chemistry
geosciencesatmosphericandoceansc
physicsandastronomy
computerandinformationsciences
mathematicsandstatistics
psychology
anthropology
economics
politicalscienceandgovernment
sociology
othersocialsciences
aerospaceaeronauticalandastronau
bioengineeringandbiomedicalengin
chemicalengineering
civilengineering
electricalelectronicsandcommunic
industrialandmanufacturingengine
materialsscienceengineering
mechanicalengineering
otherengineering
educationadministration
educationresearch
teachereducation
teachingfields
othereducation
foreignlanguagesandliterature
history
letters
otherhumanitiesandarts
businessmanagementandadministrat
communication
""".split("\n")

careerareas = [
    "Agriculture, Horticulture, & the Outdoors",
    "Business Management and Operations",
    "Clerical and Administrative",
    "Community and Social Services",
    "Construction, Extraction, and Architecture",
    "Customer and Client Support",
    "Design, Media, and Writing",
    "Education and Training",
    "Engineering",
    "Finance",
    "Health Care including Nursing",
    "Hospitality, Food, and Tourism",
    "Human Resources",
    "Information Technology",
    "Law, Compliance, and Public Safety",
    "Maintenance, Repair, and Installation",
    "Manufacturing and Production",
    "Marketing and Public Relations",
    "Performing Arts",
    "Personal Services",
    "Planning and Analysis",
    "Sales",
    "Science and Research",
    "Transportation",
    "na"]

ipedssectornames = [
    "Public, 4-year or above",
    "Private not-for-profit, less-than 2-year",
    "Administrative Unit",
    "NULL",
    "Private for-profit",
    "Private not-for-profit, 2-year",
    "Private for-profit, 4-year or above",
    "Public, 2-year",
    "Public, less-than 2-year",
    "Private for-profit, less-than 2-year",
    "Private for-profit, 2-year",
    "Private not-for-profit, 4-year or above",
    "Sector unknown (not active"
]


print(faculty_status)
print(fields_of_study)
print(departments)



query1 = "SELECT year,faculty, count(*) as N from hej where faculty=1 group by faculty,year;"


@app.route('/',methods=["GET"])
def home():
    return render_template("home.html")


@app.route('/demo1', methods=["GET", "POST"])
def demo1():
    z = demo(6)
    return render_template("demo1.html", query=query1, rows=z)

@app.route('/demo2', methods=["GET", "POST"])
def demo2():
    z = demo(1)
    results = [[x[0],x[1],x[2]] for x in z]
    return render_template("demo2.html", query=query1, rows=results)

@app.route('/facnonfac', methods=["GET", "POST"])
def facnonfac():
    z = demo(1)
    results = [[x[0],x[1],x[2]] for x in z]
    return render_template("demo2.html", query=query1, rows=results)

@app.route('/demo3', methods=["GET", "POST"])
def demo3():
    if request.method=="GET":
        return render_template("demo3.html",faculty_status=faculty_status,fields_of_study=fields_of_study, departments=departments,careerareas=careerareas,ipedssectornames=ipedssectornames,occupations=occupations)
    else:
        print(request.form)
        jobtype = request.form.getlist('jobtype')
        staff = request.form.getlist('staff')
        fac = request.form.getlist('fac')
        year = request.form.getlist('year')
        fos = request.form.getlist('fos')
        dept = request.form.getlist('dept')
        divinc = request.form.getlist('diversityandinclusion')
        rsh1 = request.form.getlist('isresearch1institution')
        careerarea = request.form.getlist('careerarea')
        ipeds = request.form.getlist('ipedssectornames')
        occs = request.form.getlist('occupations')
        min_ed = request.form.get('minimumedurequirements')
        max_ed = request.form.get('maximumedurequirements')
        min_exp = request.form.get('minimumexperiencerequirements')
        print('min ed = '+min_ed)
        query = "SELECT count(*) from hej,maintable where (hej.jobid=maintable.jobid) and "
        query += makeBoolean(jobtype)+" and "
        if (staff!=[]):
          query += " (faculty=0 and postdoctoral=0) and "
        query += makeBoolean(fos)+" and "
        query += makeYears(year)+" and "
        query += makeBoolean(dept)+" and "
        query += makeBoolean(fac) + " and "
        query += makeBoolean(divinc+rsh1) + " and "
        query += makeCareerAreas(careerarea) + " and "
        query += makeStrings('ipedssectorname',ipeds) + " and "
        query += makeStrings('occupation',occs) + " and "
        query += "minimumedurequirements >= "+min_ed+" and "
        query += "maximumedurequirements <= "+max_ed+" and "
        query += "minimumexperiencerequirements >= "+min_exp
        query += " group by hej.year"
        print(query)
        z = queryAll(query)
        print(z)
        if (z==[]):
            print("no results")
            return render_template("noResults.html",query=query)
        z1 = [x[0] for x in z]
        z2 = [makeObj(x) for x in z1]
        vals = []
        for i in range(0,len(year)):
            vals += [makeObj2(year[i],z1[i])]

        print(z)
        print(z1)
        print(z2)
        print(vals)
        years = [int(y) for y in year]
        return render_template("demo3b.html", query=query, year=years, z1=z1)

def makeObj(x):
    z={}
    z["date"]="1-May-12"
    z["close"]=x
    return z
def makeObj2(y,x):
    z={}
    z["date"]="1-Jan-"+str(y)
    z["close"]=x
    return z

def makeBoolean(list):
    if (list==[]):
        return "true"
    result = "("
    for i in range(0,len(list)-1):
        result+= list[i]+"=1 or "
    result += list[len(list)-1]+" = 1 ) "
    return result

def makeYears(list):
    if (list==[]):
        return "true"
    result = "("
    for i in range(0,len(list)-1):
        result+= " hej.year = "+list[i]+" or "
    result += " hej.year = "+ list[len(list)-1]+" ) "
    return result

def makeCareerAreas(list):
    if (list==[]):
        return "true"
    result = "("
    for i in range(0,len(list)-1):
        result+= " maintable.careerarea = '"+list[i]+"' or "
    result += " maintable.careerarea = '"+ list[len(list)-1]+"' ) "
    print('result is '+result)
    return result

def makeStrings(columnname,list):
    print("in makeStrings")
    print(list)
    if (list==[]):
        return "true"
    result = "("
    for i in range(0,len(list)-1):
        result+= " "+columnname + " = '"+list[i]+"' or "
    result += " "+columnname + " = '"+ list[len(list)-1]+"' ) "
    print('result is '+result)
    return result

def demo(n):
    switcher = {
    1: "SELECT year,faculty, count(*) as N from hej where faculty=1 group by faculty,year;",
    2: "SELECT fulltimecontingent, count(*) from hej where year =2010 group by  fulltimecontingent",
    3: "SELECT parttimecontingent, count(*) from hej where year =2010 group by  parttimecontingent",
    4: "SELECT year,count(*) from hej where (tenured=1 or tenured_track=1) group by year;",
    5: "SELECT count(*) from hej where (tenured = 1 or tenured_track =1) and (year=2007 or year=2012 or year=2017) group by year",
    6: "SELECT count(*) as N, maintable.minimumedurequirements as R from hej,maintable where (hej.jobid=maintable.jobid) and (hej.faculty = 1) and (hej.year>= 2010) group by maintable.minimumedurequirements"
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
