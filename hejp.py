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
    return render_template("home.html")

@app.route('/about',methods=["GET"])
def about():
    return render_template("about.html")

@app.route('/faculty', methods=["GET", "POST"])
def demo4a():
    if request.method=="GET":
        return render_template("faculty.html", year_range=year_range, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        requestedInstitution = request.form.getlist('institutionType')
        facultyResult = queryAll(queryFaculty(requestedYears))
        if (facultyResult==[]) :
            return render_template("noResults.html",query=query)
        faculty_df = pd.DataFrame(facultyResult, columns = ['year', 'isresearch1institution', 'postdoctoral', 'faculty', 'fouryear', 'twoyear'])
        faculty_df = faculty_df.drop(columns = ['postdoctoral'])
        if len(requestedInstitution) > 1:
            institution_1 = requestedInstitution[0]
            institution_2 = requestedInstitution[1]
            institution_1_df = calculate_faculty_share(faculty_df, institution_1, requestedYears)
            institution_2_df = calculate_faculty_share(faculty_df, institution_2, requestedYears)
            return render_template("faculty_result_two.html", institution_1_df = institution_1_df, institution_2_df = institution_2_df, year_range=year_range, institutionType = institutionType, requestedYears = requestedYears, requestedInstitution = requestedInstitution)
        elif len(requestedInstitution) == 1:
            institution_1 = requestedInstitution[0]
            institution_1_df = calculate_faculty_share(faculty_df, institution_1, requestedYears)
            return render_template("faculty_result_one.html", institution_1_df = institution_1_df, year_range=year_range, institutionType = institutionType, requestedYears = requestedYears, requestedInstitution = requestedInstitution)

@app.route('/nsfGrowth', methods=["GET", "POST"])
def nsfGrowth():
    if request.method=="GET":
        return render_template('nsfGrowth.html', fields_of_study = fields_of_study, years = year_range, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
    else:
        requestedYears = request.form.getlist('years')
        requestedFields = request.form.getlist('nsf_subject')
        column_name = ['year']
        column_name += makeFields(requestedFields).split(',')
        nsf_df = pd.DataFrame(queryAll(queryNSFGrowth(requestedFields, requestedYears)), columns = column_name)
        breakdown_year1 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[0])].drop(columns='year').sum()).reset_index()
        breakdown_year2 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[1])].drop(columns='year').sum()).reset_index()
        breakdown_year1.rename(columns={0:'count_1'}, inplace=True)
        breakdown_year2.rename(columns={0:'count_2'}, inplace=True)
        final = breakdown_year1.merge(breakdown_year2, on='index', how='inner')
        final['growth'] = round(np.true_divide(final['count_2']-final['count_1'], final['count_1']) * 100, 2)
        final = final.sort_values(by='growth', ascending=False).reset_index(drop=True)
        final_nsf = [list(final['count_1']), list(final['count_2']), list(final['growth'])]
        return render_template('nsfGrowthResult.html', final_nsf = final_nsf, requestedFields = requestedFields, requestedYears = requestedYears, fields_of_study = fields_of_study, years = year_range, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)

@app.route('/nsfGrowthResult', methods=["GET","Post"])
def nsfGrowthResult():
    return render_template("nsfGrowthResult.html")

@app.route('/allfaculty', methods=["GET","Post"])
def allfaculty():
    if request.method=="GET":
        return render_template("allfaculty.html", years = year_range, facultyStatus = faculty_status, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        queryfaculty_df = pd.DataFrame(queryAll(queryAllFaculty(requestedYears)), columns = ['year', 'ipedssectorname', 'isresearch1institution', 'postdoctoral', 'faculty', 'healthsciences', 'numberofdetailedfieldsofstudy', 'contingent', 'fulltimecontingent', 'parttimecontingent', 'tenured', 'tenured_track','fouryear', 'twoyear', 'tenureline'])
        # Mutually exclude Tenure-Line and Contingent
        queryfaculty_df['contingent'].where(((queryfaculty_df['tenureline'] > 0) & (queryfaculty_df['contingent'] < 1) |
                                        (queryfaculty_df['tenureline'] < 1) & (queryfaculty_df['contingent'] > 0)), 0, inplace=True)
        queryfaculty_df['fulltimecontingent'].where(queryfaculty_df['tenureline'] < 1, 0, inplace=True)
        queryfaculty_df['parttimecontingent'].where(queryfaculty_df['tenureline'] < 1, 0, inplace=True)
        # parse into different types of faculty faculty_status
        queryfaculty_df = queryfaculty_df[['year', 'faculty', 'isresearch1institution', 'fouryear', 'twoyear', 'tenureline', 'contingent', 'parttimecontingent', 'fulltimecontingent']]
        full_time_contingent = calculate_allfaculty('fulltimecontingent', queryfaculty_df)
        part_time_contingent = calculate_allfaculty('parttimecontingent', queryfaculty_df)
        tenure_line = calculate_allfaculty('tenureline', queryfaculty_df)
        return render_template("allfacultyResult.html", years = year_range, requestedYears = requestedYears, full_time_contingent = full_time_contingent, part_time_contingent = part_time_contingent, tenure_line = tenure_line, institutionType = institutionType)

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
        return render_template("science.html", all_sciences = all_sciences, year_range = year_range, institutionType = institutionType)
    else:
        requestedScience = request.form.getlist('sciences')
        requestedInstitution = request.form.get('institutionType')
        requestedYears = request.form.getlist('years')
        science_df = pd.DataFrame(queryAll(queryScienceOpening(requestedYears)), columns = ['year', 'isresearch1institution', 'fouryear', 'twoyear', 'biologicalandbiomedicalsciences', 'chemistry', 'computerandinformationsciences', 'geosciencesatmosphericandoceansc', 'mathematicsandstatistics', 'physicsandastronomy', 'healthsciences', 'numberofdetailedfieldsofstudy', 'faculty', 'postdoctoral', 'tenure_line', 'contingent'])
        science_df = science_df.drop(columns = ['numberofdetailedfieldsofstudy', 'postdoctoral', 'faculty'])
        if requestedInstitution != "All Higher Education":
            science_df = science_df[science_df[getInstitutionType(requestedInstitution)] == 1].drop(columns = ['isresearch1institution', 'fouryear', 'twoyear'])
        else:
            science_df = science_df.drop(columns = ['isresearch1institution', 'fouryear', 'twoyear'])

        science_opening_result = []
        total_count = []
        tenure_share_count = []
        contingent_share_count = []
        science_name = []
        for science in requestedScience:
            science_name.append(science)
            science_name.append("")
            science_result = calculate_science_opening(science_df, science, requestedYears)
            total_count += science_result[0]
            tenure_share_count += science_result[1]
            contingent_share_count += science_result[2]
        science_opening_result = [total_count, tenure_share_count, contingent_share_count]
        return render_template("scienceResult.html", requestedInstitution = requestedInstitution, requestedYears = requestedYears, requestedScience = requestedScience, science_opening_result = science_opening_result, science_name = science_name)

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
        nonfaculty_df = pd.DataFrame(queryAll(queryNonFaculty(requestedYears, requestedInstitution)), columns = ['year', requestedInstitution, 'careerarea', 'faculty', 'postdoctoral', 'public', 'private'])
        if requestedInstitution == "4-year Institutions":
            nonfaculty_df = nonfaculty_df.drop(columns = [requestedInstitution, 'faculty', 'postdoctoral'])
            public_df = pd.DataFrame(nonfaculty_df[nonfaculty_df['public'] == 1])
            public_year1 = pd.DataFrame(public_df[public_df['year'] == int(requestedYears[0])]).drop(columns=['year','private']).groupby(['careerarea']).sum().reset_index()
            public_year2 = pd.DataFrame(public_df[public_df['year'] == int(requestedYears[1])]).drop(columns=['year','private']).groupby(['careerarea']).sum().reset_index()
            public_final = public_year1.merge(public_year2, on='careerarea', how='inner')
            public_final['growth'] = round(np.true_divide(public_final['public_y']-public_final['public_x'], public_final['public_x']) * 100, 2)
            public_final = public_final.sort_values(by='growth', ascending=False)
            public_careerarea = list(public_final['careerarea'])

            private_df = pd.DataFrame(nonfaculty_df[nonfaculty_df['private'] == 1])
            private_year1 = pd.DataFrame(private_df[private_df['year'] == int(requestedYears[0])]).drop(columns=['year','public']).groupby(['careerarea']).sum().reset_index()
            private_year2 = pd.DataFrame(private_df[private_df['year'] == int(requestedYears[1])]).drop(columns=['year','public']).groupby(['careerarea']).sum().reset_index()
            private_final = private_year1.merge(private_year2, on='careerarea', how='inner')
            private_final['growth'] = round(np.true_divide(private_final['private_y']-private_final['private_x'], private_final['private_x']) * 100, 2)
            private_final = private_final.sort_values(by='growth', ascending=False)

            private_careerarea = list(private_final['careerarea'])
            for i in range(0, len(list(public_final['growth']))):
                public_careerarea[i] += "\n" + str(list(public_final['growth'])[i]) + '%'
                private_careerarea[i] += "\n" + str(list(private_final['growth'])[i]) + '%'
            public_final_list = [public_careerarea, list(public_final['public_x']), list(public_final['public_y'])]
            private_final_list = [private_careerarea, list(private_final['private_x']), list(private_final['private_y'])]
            return render_template("grown-nonfaculty-fouryear.html", public_final_list = public_final_list, private_final_list = private_final_list, year_range = year_range, institutionType = institutionType, requestedYears = requestedYears, requestedInstitution = requestedInstitution)
        else:
            nonfaculty_df = nonfaculty_df.drop(columns = [requestedInstitution, 'faculty', 'postdoctoral', 'public', 'private'])
            nonfaculty_year1 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[0])])
            nonfaculty_year1 = nonfaculty_year1.drop(columns='year').groupby(['careerarea']).apply(lambda x: x.careerarea).value_counts().to_frame().reset_index()
            nonfaculty_year2 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[1])])
            nonfaculty_year2 = nonfaculty_year2.drop(columns='year').groupby(['careerarea']).apply(lambda x: x.careerarea).value_counts().to_frame().reset_index()
            nonfaculty_final = nonfaculty_year1.merge(nonfaculty_year2, on='index', how='inner')
            nonfaculty_final = nonfaculty_final[nonfaculty_final['careerarea_y'] >= 1000]
            nonfaculty_final['growth'] = round(np.true_divide(nonfaculty_final['careerarea_y']-nonfaculty_final['careerarea_x'], nonfaculty_final['careerarea_x']) * 100, 2)
            nonfaculty_final = nonfaculty_final.sort_values(by='growth', ascending=False).reset_index(drop=True)
            area = list(nonfaculty_final['index'])
            for i in range(0, len(list(nonfaculty_final['growth']))):
                area[i] += " " + str(list(nonfaculty_final['growth'])[i]) + '%'
            nonfaculty_final_list = [area, list(nonfaculty_final['careerarea_x']), list(nonfaculty_final['careerarea_y'])]
            return render_template("grown-nonfaculty-others.html", nonfaculty_final_list = nonfaculty_final_list, year_range = year_range, institutionType = institutionType, requestedYears = requestedYears, requestedInstitution = requestedInstitution)

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
            year2table['growth'] = round((np.true_divide(year2table['Adjusted_share2']- year2table['Adjusted_share1'], year2table['Adjusted_share1'])) * 100, 2)
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
        phd_df = pd.DataFrame(queryphdShare_result, columns =['jobid','faculty', 'year', 'fouryear', 'minimumedurequirements', 'careerarea', 'occupation', 'jobtitle', 'ipedsinstitutionname'])
        top_jobs = pd.DataFrame(phd_df['occupation'].value_counts()).reset_index().rename(columns={
                'cccupation':'count'})[:8]
        phdshare = calculate_phdshare(phd_df)
        phd_top_jobs = calculate_topjob(phd_df, top_jobs)
        skill_table = pd.DataFrame(queryAll(query_top_skill(requestedYear)), columns = ['jobid', 'year', 'skill_cluster_name'])
        phd_top_skills = calculate_topskills(phd_df, top_jobs, skill_table)
        return render_template("nonfaculty-phd-result.html", year_range = year_range, institutionType = institutionType, phdshare = phdshare, top_jobs = phd_top_jobs, requestedYear = requestedYear, phd_top_skills = phd_top_skills)

@app.route('/nonfaculty-phd-result', methods = ["GET", "Post"])
def nonfaculty_phd_result():
    return render_template("nonfaculty-phd-result.html")

@app.route('/mentalandhealth', methods = ["GET", "POST"])
def mentalandhealth():
    if request.method == "GET":
        return render_template("mentalandhealth.html", year_range = year_range, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        requestedInstitution = request.form.get('institutionType')
        queryMental = queryAll(queryMentalHealth(requestedYears, requestedInstitution))
        queryMental_df = pd.DataFrame(queryMental, columns = ["skill_cluster_name", "year", "fouryear", "careerarea"])
        careers_1 = pd.DataFrame(queryMental_df['careerarea'][queryMental_df['year']==int(requestedYears[0])].value_counts()).reset_index().rename(
            columns={'careerarea':'count'})
        careers_2 = pd.DataFrame(queryMental_df['careerarea'][queryMental_df['year']==int(requestedYears[1])].value_counts()).reset_index().rename(
            columns={'careerarea':'count'})
        final = careers_1.merge(careers_2, on='index', how='inner')
        final.rename(columns={'count_x':'count_1', 'count_y':'count_2'}, inplace=True)
        final['growth'] = round(np.true_divide(final['count_2']-final['count_1'], final['count_1']) * 100, 2)
        final = final[final['count_2'] > 400]
        final = final.sort_values(by='growth', ascending=False)[:5]
        mental_health_final = [list(final['index']), list(final['count_1']), list(final['count_2']), list(final['growth'])]
        return render_template("mentalandhealth_result.html", requestedYears = requestedYears, mental_health_final = mental_health_final, requestedInstitution = requestedInstitution, year_range = year_range, institutionType = institutionType)

@app.route('/mentalandhealth_result', methods = ["GET", "POST"])
def mentalandhealth_result():
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
    # app.run(host="turing.cs-i.brandeis.edu",debug=False)
