import os
from flask import Flask
from flask import Markup
from flask import redirect
from flask import render_template
from flask import request
import psycopg2
import timeit
from collections import OrderedDict

from fieldValues import year_range, faculty_status, fields_of_study, departments, careerareas,ipedssectornames, institutionType
from occupations import occupations

project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')


@app.route('/',methods=["GET"])
def home():
    return render_template("home.html")

@app.route('/demo4', methods=["GET", "POST"])
def demo4():
    if request.method=="GET":
        return render_template("demo4.html")
    else:
        return redirect(url_for('faculty.html'))


@app.route('/faculty', methods=["GET", "POST"])
def demo4a():
    if request.method=="GET":
        queryfaculty = queryFaculty()
        queryfaculty += ") AS selected \n"
        queryfaculty += "GROUP BY year, faculty;"
        queryresult = queryAll(queryfaculty)
        faculty = [int(f) for f in (0,1)]
        groupedResult = [(f, list(count[0] for count in [eachF for eachF in queryresult if eachF[2] == f])) for f in faculty]
        years=[int(year) for year in year_range]
        return render_template("facultyDemo.html", query = queryfaculty, result = groupedResult, years = years, year_range=year_range, ipedssectornames = ipedssectornames, institutionType = institutionType)
    else:
        requestedYear = request.form.getlist('year')
        # ipeds = request.form.getlist('ipedssectornames')
        requestedInstitution = request.form.getlist('institution')
        queryfaculty = queryFaculty()
        # select year

        queryfaculty += "AND " + makeYears(requestedYear) + " "
        # select institution type
        queryfaculty += "AND " + chooseInstitution(requestedInstitution)+ ") "
        queryfaculty += "AS selected \n"
        queryfaculty += "GROUP BY year, faculty;"
        print(queryfaculty)
        facultyResult = queryAll(queryfaculty)
        if (facultyResult==[]):
            print("no results")
            return render_template("noResults.html",query=query)
        faculty = [int(f) for f in (0,1)]
        groupedResult = [(f, list(count[0] for count in [eachF for eachF in facultyResult if eachF[2] == f])) for f in faculty]
        years=[int(year) for year in requestedYear]
        # result=[(year, list(count[0] for count in [eachYear for eachYear in twoYearResult if eachYear[1] == year])) for year in years]
        return render_template("faculty.html", query = queryfaculty, result = groupedResult, years = years, year_range=year_range, ipedssectornames = ipedssectornames, institutionType = institutionType)
# @app.route('/demo4a', methods=["GET", "POST"])
# def demo4a():
#     return render_template("demo4a.html", queryTwoYear)
@app.route('/nsfGrowth', methods=["GET", "POST"])
def nsfGrowth():
    if request.method=="GET":
        # queryNSFResult = queryAll(queryNSFGrowth())
        # years = [int(y) for y in (2007, 2017)]
        # fields = []
        # result: (2007, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0)
        # groupNSF = [sum(x) for x in zip(*queryNSFResult)]
        return render_template('nsfGrowth.html', departments = departments)
    else:
        requestedDepartments = request.form.getlist('departments')
        # queryfields = queryNSFGrowth(requestedDepartments)
        queryFieldResult = []
        # [&#39;Computer and information sciences&#39;]
        # departmentList = [makeStrings(requestedDepartments)]
        for field in requestedDepartments:
            # print(queryNSFGrowth(field))
            queryFieldResult += queryAll(queryNSFGrowth(field))
        # group count for each field by year
        # grouped results: [(2007, [[2443], [3335]]), (2017, [[5089], [8843]])]
        fieldDict = OrderedDict()
        for year, *fieldCount in queryFieldResult:
            if year in fieldDict:
                fieldDict[year].append(fieldCount)
            else:
                fieldDict[year] = [fieldCount]
        # print(fieldDict)
        finalFieldDict = [(year, fieldCount) for year, fieldCount in fieldDict.items()]
        print(finalFieldDict)
        # print(queryFieldResult)
        # [Physics and astronomy, Computer and information science, Electrial electronics and communication, Teaching Fields]
        # result: [(2007, 2443), (2017, 5089), (2007, 3335), (2017, 8843), (2007, 636), (2017, 1915), (2007, 466), (2017, 875)]
        return render_template('nsfGrowthResult.html', departments = departments, queryFieldResult = queryFieldResult, finalFieldDict = finalFieldDict, requestedDepartments = requestedDepartments)
    #
    # else:
    #     return redirect(url_for('faculty.html'))

@app.route('/nsfGrowthResult', methods=["GET","Post"])
def nsfGrowthResult():
    # if request.method=="GET":
    return render_template("nsfGrowthResult.html")

@app.route('/largestNSF', methods=["GET","Post"])
def largestNSF():
    if request.method=="GET":
        largestNSF = ['Business management and administration', 'Biological and biomedical sciences', 'Health sciences']
        fieldString = ""
        fieldArray = ""
        for nsf in largestNSF:
            fieldString += "SUM(" + makeFields(nsf) + "), "
            fieldArray += makeFields(nsf) + ", "
        fieldString = fieldString[0: len(fieldString)-2]
        fieldArray = fieldArray[0: len(fieldArray)-2]
        queryLargestNSFResult = queryAll(queryLargestNSF(fieldString, fieldArray))
        resultList = list(queryLargestNSFResult[0])
        print(resultList)
        return render_template("largestNSF.html", largestNSF = largestNSF, largestNSFResult = resultList)

def queryLargestNSF(fieldString, fieldArray) :
    queryLargestNSF = "SELECT " + fieldString + " FROM "
	# queryLargestNSF += "SELECT maintable.jobid, fouryear, dummytable.* FROM maintable"
    queryLargestNSF += "(SELECT maintable.jobid, fouryear, " + fieldArray
    queryLargestNSF += " FROM maintable "
    queryLargestNSF += "RIGHT JOIN dummytable ON maintable.jobid = dummytable.jobid "
    queryLargestNSF += "WHERE fouryear = 1 "
    queryLargestNSF += "AND postdoctoral = 0 "
    queryLargestNSF += "AND (maintable.year = 2017) "
    queryLargestNSF += ")AS selected;"
    return queryLargestNSF

# queries: NSF Growth, share of faculty vs non faculty
def queryNSFGrowth(f):
    queryNSFGrowth = "SELECT year," + "SUM(" + makeFields(f) +") FROM"
    queryNSFGrowth += "(SELECT dummytable.year, "
    queryNSFGrowth += makeFields(f)
    queryNSFGrowth += "FROM dummytable "
    queryNSFGrowth += "WHERE (dummytable.healthsciences != 1 OR dummytable.numberofdetailedfieldsofstudy > 1) "
    queryNSFGrowth += "AND dummytable.faculty = 1 "
    queryNSFGrowth += "AND dummytable.postdoctoral = 0 "
    queryNSFGrowth += "AND dummytable.year = 2007 OR dummytable.year = 2017 ) AS selected "
    queryNSFGrowth += "GROUP BY year"
    return queryNSFGrowth

def queryFaculty ():
    queryfaculty = "SELECT Count(*),year,faculty From "
    queryfaculty += "(SELECT maintable.jobid, maintable.careerarea, maintable.year,"
    queryfaculty += "maintable.ipedssectorname, maintable.isresearch1institution, dummytable.postdoctoral, dummytable.healthsciences, "
    queryfaculty += "dummytable.numberofdetailedfieldsofstudy, dummytable.faculty,maintable.twoyear "
    queryfaculty += "FROM maintable  "
    queryfaculty += "INNER JOIN dummytable ON dummytable.jobid = maintable.jobid "
    queryfaculty += "WHERE dummytable.postdoctoral != 1 "
    queryfaculty += "AND maintable.careerarea NOT LIKE 'Health Care including Nursing' "
    queryfaculty += "AND (dummytable.numberofdetailedfieldsofstudy > 2 OR dummytable.healthsciences !=1) "
    return queryfaculty

def makeFields(fieldString):
    # if (fields== []):
    #     return "true"
    result = ""
    # for i in range (0, len(fields)):
    #     fieldString = fields[i]
    if fieldString == "Health sciences":
       result += "healthsciences, "
    if fieldString == "Teacher education":
       result += "teachereducation, "
    if fieldString == "Sociology":
       result += "sociology, "
    if fieldString == "Psychology":
       result += "psychology, "
    if fieldString == "Political science and government":
       result += "politicalscienceandgovernment, "
    if fieldString == "Physics and astronomy":
       result += "physicsandastronomy, "
    if fieldString == "Other social sciences":
       result += "othersocialsciences, "
    if fieldString == "Other engineering":
       result += "otherengineering, "
    if fieldString == "Mathematics and statistics":
       result += "mathematicsandstatistics, "
    if fieldString == "Letters":
       result += "letters, "
    if fieldString == "History":
       result += "history, "
    if fieldString == "Geosciences, atmospheric, and ocean sciences":
       result += "geosciencesatmosphericandoceansc, "
    if fieldString == "Foreign languages and literature":
       result += "foreignlanguagesandliterature, "
    if fieldString == "Electrical, electronics, and communication":
       result += "electricalelectronicsandcommunic, "
    if fieldString == "Economics":
       result += "economics, "
    if fieldString == "Chemistry":
       result += "chemistry, "
    if fieldString == "Business management and administration":
       result += "businessmanagementandadministrat, "
    if fieldString == "Communication":
       result += "communication, "
    if fieldString == "Biological and biomedical sciences":
       result += "biologicalandbiomedicalsciences, "
    if fieldString == "Bioengineering and biomedical engineering":
       result += "bioengineeringandbiomedicalengin, "
    if fieldString == "Agricultural sciences and natural resources":
       result += "agriculturalsciencesandnaturalre, "
    if fieldString == "Aerospace, aeronautical, and astronautical engineering":
       result += "aerospaceaeronauticalandastronau, "
    if fieldString == "Anthropology":
       result += "anthropology, "
    if fieldString == "Materials science engineering":
       result += "materialsscienceengineering, "
    if fieldString == "Mechanical engineering":
       result += "mechanicalengineering, "
    if fieldString == "Other education":
       result += "othereducation, "
    if fieldString == "Education administration":
       result += "educationadministration, "
    if fieldString == "Education research":
       result += "educationresearch, "
    if fieldString == "Teaching fields":
       result += "teachingfields, "
    if fieldString == "Industrial and manufacturing engineering":
       result += "industrialandmanufacturingengine, "
    if fieldString == "Computer and information sciences":
       result += "computerandinformationsciences, "
    if fieldString == "Chemical engineering":
       result += "chemicalengineering, "
    if fieldString == "Civil engineering":
       result += "civilengineering, "
    if fieldString == "Other humanities and arts":
       result+= "otherhumanitiesandarts, "
    if fieldString == "":
       result+= "true"
    result = result[0: len(result)-2] +   " "
    return result


def makeYears(year):
    if (year==[]):
        return "true"
    result = "("
    for i in range(0,len(year)-1):
        result+= "dummytable.year = "+year[i]+" or "
    result += " dummytable.year = "+ year[len(year)-1]+" ) "
    return result

def makeStrings(list):
    if (list==[]):
        return "true"
    result = []
    for i in range(0,len(list)):
        result.append(list[i])
    print(result)
    return result

def chooseInstitution(institution):
    if (institution==[] or institution[0] == 'All Higher Education'):
        return "true"
    result = "( "
    for i in range(0, len(institution)):
        if institution[i] == 'R1 Universities':
            result += 'isresearch1institution = 1 or '
        if institution[i] == '4-year Institutions':
            result += 'fouryear = 1 or '
        if institution[i] == '2-year Institutions':
            result += 'twoyear = 1 or'


    print(result)
    result = result[0: len(result)-3] + " )"
    return result

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




if __name__ == "__main__":
    app.run(debug=True)
