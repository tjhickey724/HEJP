from __future__ import division
import os
from flask import Flask
from flask import Markup
from flask import redirect
from flask import render_template
from flask import request
import psycopg2
import timeit
from collections import OrderedDict

from fieldValues import *
from occupations import occupations
from nsfFields import *

project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')


@app.route('/home',methods=["GET"])
def home():
    return render_template("home.html")

@app.route('/about',methods=["GET"])
def about():
    return render_template("about.html")

# @app.route('/demo4', methods=["GET", "POST"])
# def demo4():
#     if request.method=="GET":
#         return render_template("demo4.html")
#     else:
#         return redirect(url_for('faculty.html'))

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
        years = [int(y) for y in year_range]
        return render_template('nsfGrowth.html', fields_of_study = fields_of_study, years = years, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
    else:
        requestedYears = request.form.getlist('years')
        requestedDepartments = request.form.getlist("fields_of_study")
        # queryfields = queryNSFGrowth(requestedDepartments)
        queryFieldResult = []
        # [&#39;Computer and information sciences&#39;]
        # departmentList = [makeStrings(requestedDepartments)]
        for field in requestedDepartments:
            # print(queryNSFGrowth(field))
            queryFieldResult += queryAll(queryNSFGrowth(field, requestedYears))
        # group count for each field by year
        # grouped results:
        fieldDict = OrderedDict()
        for year, *fieldCount in queryFieldResult:
            if year in fieldDict:
                fieldDict[year].append(fieldCount)
            else:
                fieldDict[year] = [fieldCount]
        # print(fieldDict)
        finalFieldDict = [(year, fieldCount) for year, fieldCount in fieldDict.items()]
        print(finalFieldDict)
        # [(2011, [[2432], [3635]]), (2012, [[3380], [4587]]), (2015, [[2936], [5201]]), (2016, [[2706], [6491]])]
        # print(queryFieldResult)
        # [Physics and astronomy, Computer and information science, Electrial electronics and communication, Teaching Fields]
        # result: [(2007, 2443), (2017, 5089), (2007, 3335), (2017, 8843), (2007, 636), (2017, 1915), (2007, 466), (2017, 875)]
        return render_template('nsfGrowthResult.html', departments = departments, queryFieldResult = queryFieldResult, finalFieldDict = finalFieldDict, requestedDepartments = requestedDepartments, requestedYears = requestedYears, years = year_range, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
    #
    # else:
    #     return redirect(url_for('faculty.html'))

@app.route('/nsfGrowthResult', methods=["GET","Post"])
def nsfGrowthResult():
    # if request.method=="GET":
    return render_template("nsfGrowthResult.html")

@app.route('/allfaculty', methods=["GET","Post"])
def allfaculty():
    if request.method=="GET":
        return render_template("allfaculty.html", years = year_range, facultyStatus = faculty_status, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        requestedFaculty = request.form.getlist('status')
        queryFacultyResult = []
        institutionList = ["R1 Universities","4-year Institutions","2-year Institutions","All Higher Education"]
        for institution in institutionList:
            queryFacultyResult += queryAll(queryAllFaculty(requestedFaculty, requestedYears, institution))
        print(queryFacultyResult)
        #[(2012, 852), (2014, 1504), (2012, 5565), (2014, 7541), (2012, 1427), (2014, 2365), (2012, 7045), (2014, 9978)]

        groupedFaculty = OrderedDict()
        for year, count in queryFacultyResult:
            if year in groupedFaculty:
                groupedFaculty[year].append(count)
            else:
                groupedFaculty[year] = [count]
        finalFaculty = [(year, count) for year, count in groupedFaculty.items()]
        print(finalFaculty)
        return render_template("allfacultyResult.html", groupedFaculty = finalFaculty, requestedYears = requestedYears, requestedFaculty = requestedFaculty, institutionType = institutionList)

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

@app.route('/science', methods=["GET","Post"])
def science_opening():
    if request.method=="GET":
        return render_template("science.html", all_sciences = all_sciences, year_range = year_range)
    else:
        requestedScience = request.form.getlist('sciences');
        requestedYears = request.form.getlist('years');
        yearString =""
        for y in requestedYears:
            yearString += str(y) +", "
        yearString = yearString[0: len(yearString)-2]
        category = ["AND contingent = 1 ", "AND tenureline = 1 ", '']
        query_science_opening = []
        contingent = []
        total_year_result = []
        tenureline = []
        for f in requestedScience:
            for c in category:
                if c == "AND contingent = 1 ":
                    contingent += queryAll(queryScienceOpening(c,f,requestedYears))
                if c == "AND tenureline = 1 ":
                    tenureline += queryAll(queryScienceOpening(c,f,requestedYears))
                if c == '':
                    total_year_result += queryAll(queryScienceOpening(c,f,requestedYears))
        query_science_opening.append(contingent)
        query_science_opening.append(tenureline)
        query_science_opening.append(total_year_result)
        print(query_science_opening)

        groupedFirst = []
        for n in query_science_opening:
            grouped = OrderedDict()
            for count, y in n:
                if y in grouped:
                    grouped[y].append(count)
                else:
                    grouped[y] = [count]
            final_data = [(count, y) for count, y in grouped.items()]
            groupedFirst.append(final_data)

        science = OrderedDict()
        for g in groupedFirst:
            for year, count in g:
                if year in science:
                    science[year].append(count)
                else:
                    science[year] = [count]
        final_science = [(year,count) for year,count in science.items()]
        print(final_science)
        #[(2012, [[380, 1455, 2214], [9, 86, 101]]), (2015, [[425, 1704, 2643], [26, 137, 181]])]
        return render_template("scienceResult.html", all_sciences = all_sciences, year_range = year_range, final_science = final_science, requestedScience = requestedScience, requestedYears =requestedYears, yearString = yearString)

@app.route('/scienceResult', methods=["GET","Post"])
def science_opening_result():
    return render_template("scienceResult.html")

@app.route('/grown-nonfaculty', methods=["GET","Post"])
def grown_nonfaculty():
    if request.method=="GET":
        return render_template("grown-nonfaculty.html", years = year_range, institutionType = institutionType)
    else:
        requestedInstitution = request.form.get('institutionType')
        requestedYears = request.form.getlist('years')
        query_nonfaculty = queryAll(queryNonFaculty(requestedYears, requestedInstitution))
        print(query_nonfaculty)
        group_nonfaculty = OrderedDict()
        selected_area = []
        for area, y, data in query_nonfaculty:
            if area not in selected_area:
                selected_area.append(area)
            if y in group_nonfaculty:
                group_nonfaculty[y].append(data)
            else:
                group_nonfaculty[y] = [data]
        final_group_nonfaculty = [(y, data) for y, data in group_nonfaculty.items()]
        return render_template("grown-nonfaculty-result.html", year_range = year_range, institutionType = institutionType, years = requestedYears, institution = requestedInstitution, query_nonfaculty = query_nonfaculty, final_group_nonfaculty = final_group_nonfaculty, selected_area = selected_area)

def queryNonFaculty(years, institution):
    queryNonFaculty = "SELECT careerarea, year, COUNT(careerarea) FROM "
    queryNonFaculty += "(SELECT dummytable.year, isresearch1institution, careerarea, faculty, postdoctoral "
    queryNonFaculty += "FROM maintable "
    queryNonFaculty += "Inner join dummytable on maintable.jobid = dummytable.jobid "
    queryNonFaculty += "WHERE faculty = 0"
    queryNonFaculty += "AND postdoctoral != 1"
    queryNonFaculty += "AND careerarea NOT LIKE 'Health Care including Nursing' "
    queryNonFaculty += "AND careerarea NOT LIKE 'Agriculture, Horticulture, & the Outdoors' "
    queryNonFaculty += "AND careerarea NOT LIKE 'Personal Services' "
    queryNonFaculty += "AND careerarea NOT LIKE 'Transportation' "
    queryNonFaculty += "AND careerarea NOT LIKE 'Performing Arts' "
    queryNonFaculty += "AND careerarea NOT LIKE 'na' "
    queryNonFaculty += "AND " + makeYears(years) + " "
    queryNonFaculty += "AND " + getInstitutionDummy(institution) + ") AS selected "
    queryNonFaculty += "GROUP BY year, careerarea;"
    return queryNonFaculty

def queryScienceOpening(category, f, requestedYears):
    queryScienceOpening = "SELECT "
    queryScienceOpening += "SUM( " + makeFields(f) + " ), year FROM "
    queryScienceOpening += "(SELECT dummytable.year, isresearch1institution, ipedssectorname, fouryear, twoyear, "
    queryScienceOpening += "biologicalandbiomedicalsciences, chemistry, computerandinformationsciences, "
    queryScienceOpening += "geosciencesatmosphericandoceansc, mathematicsandstatistics, physicsandastronomy, "
    queryScienceOpening += "healthsciences,numberofdetailedfieldsofstudy,faculty,postdoctoral,tenureline, "
    queryScienceOpening += "tenured_track, contingent "
    queryScienceOpening += "FROM maintable "
    queryScienceOpening += "INNER JOIN dummytable on maintable.jobid = dummytable.jobid "
    queryScienceOpening += "WHERE postdoctoral != 1 "
    queryScienceOpening += "AND faculty = 1 "
    queryScienceOpening += "AND isresearch1institution = 1 "
    queryScienceOpening += "AND (numberofdetailedfieldsofstudy > 2 OR healthsciences != 1) "
    queryScienceOpening += "AND " + makeYears(requestedYears) + " "
    queryScienceOpening += "AND (ipedssectorname NOT LIKE 'NULL' OR ipedssectorname NOT LIKE '%Sector unknown (not active%') "
    queryScienceOpening += category
    queryScienceOpening += "AND (" + makeFields(f) + "= 1" + ")) AS selected "
    queryScienceOpening += "GROUP BY year"
    return queryScienceOpening

def queryAllFaculty (requestedFaculty, requestedYears, institution):
    queryAllFaculty = "SELECT year, COUNT(" + makeFacultyStatus(requestedFaculty) + ") FROM"
    queryAllFaculty += "(SELECT maintable.year, ipedssectorname, "
    queryAllFaculty += "isresearch1institution, "
    queryAllFaculty += "postdoctoral, faculty, healthsciences, "
    queryAllFaculty += "numberofdetailedfieldsofstudy, "
    queryAllFaculty += makeFacultyStatus(requestedFaculty)
    queryAllFaculty += "FROM maintable "
    queryAllFaculty += "INNER JOIN dummytable on maintable.jobid = dummytable.jobid "
    queryAllFaculty += "WHERE postdoctoral != 1 AND faculty = 1 "
    queryAllFaculty += "AND (numberofdetailedfieldsofstudy > 2 OR healthsciences != 1) "
    queryAllFaculty += "AND "+ makeYears(requestedYears)
    queryAllFaculty += "AND (ipedssectorname NOT LIKE 'NULL' AND ipedssectorname NOT LIKE '%Sector unknown (not active%') "
    queryAllFaculty += "AND " + getFacultyDummy(requestedFaculty)
    queryAllFaculty += "AND " + getInstitutionDummy(institution)
    queryAllFaculty += ") AS selected "
    queryAllFaculty += "GROUP BY year;"
    return queryAllFaculty

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
def queryNSFGrowth(f, requestedYears):
    queryNSFGrowth = "SELECT year," + "SUM(" + chooseFieldsOfStudy(f) +") FROM "
    queryNSFGrowth += "(SELECT dummytable.year, " + getFieldsName() + ", " + chooseFieldsOfStudy(f) + " "
    # queryNSFGrowth += makeFields(f)
    queryNSFGrowth += "FROM dummytable "
    queryNSFGrowth += "WHERE (dummytable.healthsciences != 1 OR dummytable.numberofdetailedfieldsofstudy > 1) "
    queryNSFGrowth += "AND dummytable.faculty = 1 "
    queryNSFGrowth += "AND dummytable.postdoctoral = 0 "
    queryNSFGrowth += "AND " + getFieldsDummy(f)
    queryNSFGrowth += "AND " + makeYears(requestedYears) + ") AS selected "
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

#get the variable name as a string for fields in database
def getFieldsName():
    allFields = ""
    for i in range(0, len(database_fields)):
        allFields += database_fields[i] + ", "
    allFields = allFields[0: len(allFields)-2]
    return allFields

def makeFacultyStatus (requestedFaculty):
    if (requestedFaculty == []):
        return "true"
    if (requestedFaculty[0] == 'Full-Time Contingent Positions'):
        return "fulltimecontingent "
    if (requestedFaculty[0] == 'Part-Time Contingent Positions'):
        return "parttimecontingent "
    if (requestedFaculty[0] == 'Tenure Line Positions'):
        return "tenureline "

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
    if fieldString == "Agricultural sciences and natural sciences":
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
       result += "otherhumanitiesandarts, "
    if fieldString == "":
       result += "true"
    result = result[0: len(result)-2] +   " "
    return result

def getFacultyDummy(requestedFaculty):
    if (requestedFaculty ==[]):
        return "true"
    if (requestedFaculty[0] == 'Full-Time Contingent Positions'):
        return "fulltimecontingent = 1"
    if (requestedFaculty[0] == 'Part-Time Contingent Positions'):
        return "parttimecontingent = 1"
    if (requestedFaculty[0] == 'Tenure Line Positions'):
        return "tenureline = 1"

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

def getInstitutionDummy(institution):
    if (institution == 'All Higher Education'):
        return "true"
    if (institution == 'R1 Universities'):
        return "isresearch1institution = 1"
    if (institution == '4-year Institutions'):
        return "fouryear = 1"
    if (institution == '2-year Institutions'):
        return "twoyear = 1"

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
        result = result[0: len(result)-3] + " )"
        return result

# return each field individually
def getFieldsDummy(fields):
    #if (fields == []):
        #return "true"
    # for i in range(0, len(fields)):
    result = ""
    if (fields == 'Life sciences'):
        result += 'fs_lifesciences = 1 '
    if (fields == 'Physical sciences and earth sciences'):
        result += 'fs_physicalsciencesandearthsciences = 1 '
    if (fields == 'Mathematics and computer sciences'):
        result += 'fs_mathematicsandcomputersciences = 1'
    if (fields == 'Psychology and social sciences'):
        result += 'fs_psychologyandsocialsciences = 1 '
    if (fields == 'Engineering'):
        result += 'fs_engineering = 1 '
    if (fields == 'Education'):
        result += 'fs_education = 1 '
    if (fields == 'Humanities and arts'):
        result += 'fs_humanitiesandarts = 1 '
    if (fields == 'Others'):
        result += 'fs_others = 1 '
    return result

def chooseFieldsOfStudy(fields):
    result = ""
    if (fields == 'Life sciences'):
        result += 'fs_lifesciences'
    if (fields == 'Physical sciences and earth sciences'):
        result += 'fs_physicalsciencesandearthsciences'
    if (fields == 'Mathematics and computer sciences'):
        result += 'fs_mathematicsandcomputersciences'
    if (fields == 'Psychology and social sciences'):
        result += 'fs_psychologyandsocialsciences'
    if (fields == 'Engineering'):
        result += 'fs_engineering'
    if (fields == 'Education'):
        result += 'fs_education'
    if (fields == 'Humanities and arts'):
        result += 'fs_humanitiesandarts'
    if (fields == 'Others'):
        result += 'fs_others'
    return result

def makeCareerArea(careerArea):
    return "careerarea LIKE " + "'"+ careerArea+ "'"


def queryAll(query):
    """ Connect to the PostgreSQL database server """
    conn = None
    result = None
    try:
        # read connection parameters
        conn_string = "host='localhost' dbname='HEJP' user='postgres' password='a12s34d56'"
        # conn_string = "dbname='hejp' user='hejp' password='hejp2019zzyy'"


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
    # app.run(debug=True)
    app.run(host='0.0.0.0',debug=True)
