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

project_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__,
            static_url_path='',
            static_folder='static')


@app.route('/',methods=["GET"])
def home():
    return render_template("home.html")

@app.route('/about',methods=["GET"])
def about():
    return render_template("about.html")

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
        years = [int(y) for y in year_range]
        return render_template('nsfGrowth.html', fields_of_study = fields_of_study, years = years, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
    else:
        requestedYears = request.form.getlist('years')
        requestedDepartments = request.form.getlist('fields_of_study')
        requestedFields = request.form.getlist('nsf_subject')
        # queryfields = queryNSFGrowth(requestedDepartments)
        queryFieldResult = []
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

@app.route('/career', methods = ["GET", "Post"])
def career():
    if request.method == "GET":
        return render_template("career.html", year_range = year_range, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        requestedInstitution = request.form.get('institutionType')
        requestedVisualization = request.form.get('visualizationType')
        year1 = int(requestedYears[0])
        year2 = int(requestedYears[1])
        type1 = False
        queryCareerResult = queryAll(queryCareer(requestedYears, requestedInstitution))
        if requestedVisualization == "most_requested_skill":
            type1 = True
            year1Result = OrderedDict()
            year2Result = OrderedDict()
            for year, count, name in queryCareerResult:
                if year == year1:
                    if name in year1Result:
                        year1Result[name].append(count)
                    else:
                        year1Result[name] = count
                if year == year2:
                    if name in year2Result:
                        year2Result[name].append(count)
                    else:
                        year2Result[name] = count
            year1Result = [(name, count) for name, count in year1Result.items()]
            year2Result = [(name, count) for name, count in year2Result.items()]
            year1Result = year1Result[:10]
            year2Result = year2Result[:10]
            year1max = [r[1] for r in year1Result[:1]]
            year2max = [r[1] for r in year2Result[:1]]
            share2 = [round(((x / year2max[0]) * 100), 1) for x in [r[1] for r in year2Result]]
            year2Final = []
            for i in range(0,10):
                year2Final.append((share2[i],) + year2Result[i])
            share1 = [round(((x / year1max[0]) * 100), 1) for x in [r[1] for r in year1Result]]
            year1Final = []
            for i in range(0,10):
                year1Final.append((share1[i],) + year1Result[i])
            return render_template("careerResult.html", requestedYears = requestedYears, requestedInstitution = requestedInstitution, year_range = year_range, institutionType = institutionType, year1Final = year1Final, year2Final = year2Final, type1 = type1)
        if requestedVisualization == "fastest_growing":
            queryTable = pd.DataFrame(queryCareerResult, columns =['Year', 'Count', 'SkillName'])
            year1table = queryTable[queryTable['Year'] == year1].sort_values(by=['Count'], ascending=False)
            year2table = queryTable[queryTable['Year'] == year2].sort_values(by=['Count'], ascending=False)
            max1 = year1table['Count'].iloc[0]
            max2 = year2table['Count'].iloc[0]
            year2table = year2table.merge(year1table, on = 'SkillName', how = 'inner')
            year2table['Adjusted_share1'] = [x / max1 for x in year2table['Count_y']]
            year2table['Adjusted_share2'] = [x / max2 for x in year2table['Count_x']]
            year2table['growth'] = round((np.true_divide(year2table['Adjusted_share2']- year2table['Adjusted_share1'], year2table['Adjusted_share2'])) * 100, 2)
            year2table = year2table.sort_values(by=['growth'], ascending=False)
            subset = year2table[['SkillName','Count_y', 'Count_x', 'growth']]
            year2table = subset.to_records(index = False).tolist()
            skill_name = []
            year1count = []
            year2count = []
            growth = []
            i = 0
            for ele in year2table[:10]:
                skill_name.append(year2table[i][0])
                year1count.append(year2table[i][1])
                year2count.append(year2table[i][2])
                growth.append(year2table[i][3])
                i = i + 1
            final = [skill_name, year1count, year2count, growth]
            return render_template("careerResult2.html", requestedYears = requestedYears, requestedInstitution = requestedInstitution, year_range = year_range, institutionType = institutionType, final = final, year2table = year2table[:10])

@app.route('/careerResult', methods = ["GET", "Post"])
def careerResult():
    if request.method == "GET":
        return render_template("careerResult.html")

@app.route('/careerResult2', methods = ["GET", "Post"])
def careerResult2():
    if request.method == "GET":
        return render_template("careerResult2.html")

@app.route('/nonfaculty-phd', methods = ["GET", "Post"])
def nonfaculty_phd():
    if request.method == "GET":
        return render_template("nonfaculty-phd.html", year_range = year_range, institutionType = institutionType)
    else:
        requestedYear = request.form.get('years')
        requestedInstitution = request.form.get('institutionType')
        queryphdShare_result = queryAll(commonQueryPhd([requestedYear], requestedInstitution))
        phd_df = pd.DataFrame(queryphdShare_result, columns =['faculty', 'year', 'fouryear', 'minimumedurequirements', 'careerarea', 'occupation', 'jobtitle', 'ipedsinstitutionname'])
        phd_share = pd.DataFrame(phd_df['careerarea'].value_counts()).reset_index().rename(columns={
            'careerarea':'count'})
        phd_share = phd_share.sort_values(by=['count'], ascending=False)
        phd_share_res = phd_share.to_records(index = False).tolist()
        career_area = []
        count = []
        other_count = 0;
        for i in range(0, len(phd_share_res)):
            if i < 9:
                career_area.append(phd_share_res[i][0])
                count.append(phd_share_res[i][1])
            else:
                other_count += phd_share_res[i][1]
        career_area.append('Others')
        count.append(other_count)
        phdshare = [career_area, count]
        top_jobs = pd.DataFrame(phd_df['occupation'].value_counts()).reset_index().rename(columns={
            'cccupation':'count'})[:8]
        top_jobs_res = top_jobs.to_records(index = False).tolist()
        job_count = []
        job_name = []
        for i in range(0, len(top_jobs_res)):
            job_name.append(top_jobs_res[i][0])
            job_count.append(top_jobs_res[i][1])
        top_jobs_final = [job_name, job_count]
        return render_template("nonfaculty-phd-result.html", year_range = year_range, institutionType = institutionType, phdshare = phdshare, top_jobs = top_jobs_final, requestedYear = requestedYear)

@app.route('/nonfaculty-phd-result', methods = ["GET", "Post"])
def nonfaculty_phd_result():
    return render_template("nonfaculty-phd-result.html")

@app.route('/mentalandhealth', methods = ["GET", "POST"])
def mentalandhealth():
    if request.method == "GET":
        return render_template("mentalandhealth.html", year_range = year_range, institutionType = institutionType)
    else:
        requestedYear = request.form.get('years')
        requestedInstitution = request.form.get('institutionType')
        queryMental = queryAll(queryMentalHealth([requestedYear], requestedInstitution))
        queryMental_df = pd.DataFrame(queryMental, columns = ["skill_cluster_name", "year", "fouryear", "careerarea"])
        return render_template("mentalandhealth_result.html")

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
    app.run(debug=True)
    # app.run(host='0.0.0.0',debug=True)
