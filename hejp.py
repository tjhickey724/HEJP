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
        return render_template('nsfGrowth.html', institutionType = institutionType, fields_of_study = fields_of_study, years = year_range, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
    else:
        requestedYears = request.form.getlist('years')
        requestedFields = request.form.getlist('nsf_subject')
        requestedInstitution = request.form.get('institutionType')
        column_name = ['year', 'twoyear', 'fouryear', 'isresearch1institution', 'public', 'private']
        field_string = makeFields(requestedFields)
        column_name += field_string[0:len(field_string) - 1].split(', ')
        nsf_df = pd.DataFrame(queryAll(queryNSFGrowth(requestedFields, requestedYears)), columns = column_name)
        if requestedInstitution == 'R1 Universities' or requestedInstitution == '4-Year Institutions':
            nsf_df = nsf_df[nsf_df[getInstitutionType(requestedInstitution)] == 1].drop(columns=['isresearch1institution','twoyear', 'fouryear'])
            breakdown_year1 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[0])].drop(columns='year'))
            breakdown_year2 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[1])].drop(columns='year'))
            final_nsf = calculate_merge_nsfGrowth(breakdown_year1, breakdown_year2, requestedFields)
            # final_nsf = [list(final['count_1']), list(final['count_2']), list(final['growth'])]
            return render_template('nsfGrowthResult.html', final_nsf = final_nsf, requestedInstitution = requestedInstitution, requestedFields = requestedFields, requestedYears = requestedYears, fields_of_study = fields_of_study, years = year_range, math = math, psychology = psychology, others = others, engineering = engineering, humanities = humanities, education = education, physicalSciences = physicalSciences, lifeSciences = lifeSciences)
        else:
            nsf_df = nsf_df.drop(columns=['public', 'private'])
            if requestedInstitution == '2-Year Institutions':
                nsf_df = nsf_df[nsf_df[getInstitutionType(requestedInstitution)] == 1].drop(columns=['isresearch1institution','twoyear', 'fouryear'])
            else:
                nsf_df = nsf_df.drop(columns=['isresearch1institution','twoyear', 'fouryear'])
            breakdown_year1 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[0])].drop(columns='year'))
            breakdown_year2 = pd.DataFrame(nsf_df[nsf_df['year'] == int(requestedYears[1])].drop(columns='year'))
            return render_template('nsfGrowthResult.html')

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
            science_name_year = []
            # parse the name into multiline label
            science_name_year += science.split(' ')
            science_name_year.append(requestedYears[0])
            science_name.append(science_name_year)
            science_name.append(requestedYears[1])
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
        if requestedInstitution == "4-year Institutions" or requestedInstitution == "R1 Universities":
            nonfaculty_df = nonfaculty_df.drop(columns = [requestedInstitution, 'faculty', 'postdoctoral'])
            # total count
            total_year1 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[0])]).drop(columns=['year', 'public', 'private']).groupby('careerarea').apply(lambda x: x.careerarea).value_counts().reset_index()
            total_year2 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[1])]).drop(columns=['year', 'public', 'private']).groupby('careerarea').apply(lambda x: x.careerarea).value_counts().reset_index()
            total_final = total_year1.merge(total_year2, on='index', how='inner')
            total_final  = total_final [total_final['careerarea_y'] >= 1500]
            total_final['growth'] = round(np.true_divide(total_final['careerarea_y']-total_final['careerarea_x'], total_final['careerarea_x']) * 100, 1)
            total_final = total_final.sort_values(by='growth', ascending=False)
            total_careerarea = list(total_final['index'])
            for j in range(0, len(list(total_final['growth']))):
                total_careerarea[j] += "  (" + str(list(total_final['growth'])[j]) + '%)'
            total_final_list = [total_careerarea, list(total_final['careerarea_x']), list(total_final['careerarea_y'])]
            # create growth rate table
            top_ten = total_final[['index', 'growth']][:10]
            top_ten = top_ten.rename(columns = {'index': 'careerarea'})
            # public breakout
            public_df = pd.DataFrame(nonfaculty_df[nonfaculty_df['public'] == 1])
            public_year1 = pd.DataFrame(public_df[public_df['year'] == int(requestedYears[0])]).drop(columns=['year','private']).groupby(['careerarea']).sum().reset_index()
            public_year2 = pd.DataFrame(public_df[public_df['year'] == int(requestedYears[1])]).drop(columns=['year','private']).groupby(['careerarea']).sum().reset_index()
            public_final = public_year1.merge(public_year2, on='careerarea', how='inner')
            public_final['growth'] = round(np.true_divide(public_final['public_y']-public_final['public_x'], public_final['public_x']) * 100, 1)
            # merge the public growth with top ten table
            public_final = public_final.sort_values(by='growth', ascending=False).reset_index().drop(columns = 'index')
            public_growth = public_final[['careerarea', 'growth']]

            top_ten = top_ten.merge(public_growth, on = 'careerarea', how = 'inner')
            # get the public relative rank
            public_rank = top_ten[['careerarea', 'growth_y']].sort_values(by='growth_y', ascending=False).reset_index().drop(columns=['index', 'growth_y'])
            public_rank.index = np.arange(1, len(public_rank)+1)
            public_rank['public_rank'] = public_rank.index
            top_ten = top_ten.merge(public_rank, on = 'careerarea', how = 'inner')


            public_final = public_final[public_final['public_y'] >= 1500]
            public_careerarea = list(public_final['careerarea'])
            # private breakdown
            private_df = pd.DataFrame(nonfaculty_df[nonfaculty_df['private'] == 1])
            private_year1 = pd.DataFrame(private_df[private_df['year'] == int(requestedYears[0])]).drop(columns=['year','public']).groupby(['careerarea']).sum().reset_index()
            private_year2 = pd.DataFrame(private_df[private_df['year'] == int(requestedYears[1])]).drop(columns=['year','public']).groupby(['careerarea']).sum().reset_index()
            private_final = private_year1.merge(private_year2, on='careerarea', how='inner')
            private_final['growth'] = round(np.true_divide(private_final['private_y']-private_final['private_x'], private_final['private_x']) * 100, 1)
            private_final = private_final.sort_values(by='growth', ascending=False).reset_index().drop(columns = 'index')
            private_growth = private_final[['careerarea', 'growth']]

            top_ten = top_ten.merge(private_growth, on = 'careerarea', how = 'inner')
            # get the relative rank for private
            private_rank = top_ten[['careerarea', 'growth']].sort_values(by='growth', ascending=False).reset_index().drop(columns=['index', 'growth'])
            private_rank.index = np.arange(1, len(private_rank)+1)
            private_rank['private_rank'] = private_rank.index
            top_ten = top_ten.merge(private_rank, on = 'careerarea', how = 'inner')

            private_final = private_final[private_final['private_y'] >= 1500]
            # calculate growth
            private_careerarea = list(private_final['careerarea'])
            for i in range(0, len(list(public_final['growth']))):
                public_careerarea[i] += "  (" + str(list(public_final['growth'])[i]) + '%)'
            for i in range(0, len(list(private_final['growth']))):
                private_careerarea[i] += "  (" + str(list(private_final['growth'])[i]) + '%)'
            public_final_list = [public_careerarea, list(public_final['public_x']), list(public_final['public_y'])]
            private_final_list = [private_careerarea, list(private_final['private_x']), list(private_final['private_y'])]
            top_ten_list = top_ten.values.tolist()
            return render_template("grown-nonfaculty-fouryear.html", top_ten_list = top_ten_list, total_final_list = total_final_list, public_final_list = public_final_list, private_final_list = private_final_list, year_range = year_range, institutionType = institutionType, requestedYears = requestedYears, requestedInstitution = requestedInstitution)
        else:
            nonfaculty_df = nonfaculty_df.drop(columns = [requestedInstitution, 'faculty', 'postdoctoral', 'public', 'private'])
            nonfaculty_year1 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[0])])
            nonfaculty_year1 = nonfaculty_year1.drop(columns='year').groupby(['careerarea']).apply(lambda x: x.careerarea).value_counts().to_frame().reset_index()
            nonfaculty_year2 = pd.DataFrame(nonfaculty_df[nonfaculty_df['year'] == int(requestedYears[1])])
            nonfaculty_year2 = nonfaculty_year2.drop(columns='year').groupby(['careerarea']).apply(lambda x: x.careerarea).value_counts().to_frame().reset_index()
            nonfaculty_final = nonfaculty_year1.merge(nonfaculty_year2, on='index', how='inner')
            nonfaculty_final = nonfaculty_final[nonfaculty_final['careerarea_y'] >= 1500]
            nonfaculty_final['growth'] = round(np.true_divide(nonfaculty_final['careerarea_y']-nonfaculty_final['careerarea_x'], nonfaculty_final['careerarea_x']) * 100, 1)
            nonfaculty_final = nonfaculty_final.sort_values(by='growth', ascending=False).reset_index(drop=True)
            area = list(nonfaculty_final['index'])
            for i in range(0, len(list(nonfaculty_final['growth']))):
                area[i] += "  (" + str(list(nonfaculty_final['growth'])[i]) + '%)'
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


@app.route('/career_breakdown', methods = ["GET", "Post"])
def career_breakdown():
    if request.method == "GET":
        return render_template("career_breakdown.html", year_range = year_range, institutionType = institutionType)
    else:
        requestedYears = request.form.getlist('years')
        requestedInstitution = request.form.get('institutionType')
        career_df = pd.DataFrame(queryAll(queryCareerBreakout(requestedInstitution,requestedYears)), columns = ['jobid', 'year', 'occupation', 'careerarea', 'isresearch1institution', 'fouryear', 'twoyear', 'faculty', 'postdoctoral'])
        career_df = career_df.drop(columns = ['faculty', 'postdoctoral'])
        skill_df = pd.DataFrame(queryAll(querySkill(requestedYears)), columns = ['jobid', 'year', 'skill_cluster_name'])
        skill_df_year1 = skill_df[skill_df['year'] == int(requestedYears[0])]
        skill_df_year2 = skill_df[skill_df['year'] == int(requestedYears[1])]
        if requestedInstitution == 'All Higher Education':
            career_df = career_df.drop(columns = ['isresearch1institution', 'twoyear', 'fouryear'])
        else:
            career_df = career_df[career_df[getInstitutionType(requestedInstitution)] == 1].drop(columns = ['isresearch1institution', 'twoyear', 'fouryear'])
        careers = ['Business Management and Operations']
        # careers = ['Education and Training', 'Science and Research', 'Counseling and Religious Life','Business Management and Operations', 'Analysis']
        career_top_occupation = []
        occupation_top_skills = []
        top_skills_name = []
        growth = []
        for career in careers:
            aux_table = career_df[(career_df['careerarea']==career)]
            occ_1 = pd.DataFrame(aux_table[aux_table['year']== int(requestedYears[0])]['occupation'].value_counts()).reset_index().rename(
                columns={'occupation':'count_1', 'index':'occupation_1'})
            occ_1 = occ_1[occ_1['occupation_1'] != 'College Professor / Instructor']
            occ_2 = pd.DataFrame(aux_table[aux_table['year']== int(requestedYears[1])]['occupation'].value_counts()).reset_index().rename(
                columns={'occupation':'count_2', 'index':'occupation_2'})
            occ_2 = occ_2[occ_2['occupation_2'] != 'College Professor / Instructor']
            occ_total = occ_1[:10].join(occ_2[:10])
            # print(occ_total)
            combine = []
            combine.append(occ_total.values.tolist())
            career_top_occupation += combine
            # get the top skills
            career_table = aux_table[(aux_table['year']== int(requestedYears[1]))&(aux_table['occupation']==occ_2.iloc[0]['occupation_2'])]
            career_table_year1 = aux_table[(aux_table['year']== int(requestedYears[0]))&(aux_table['occupation']==occ_1.iloc[0]['occupation_1'])]
            total_year1 = career_table_year1.shape[0]
            total_year2 = career_table.shape[0]
            # career_table_year1['adjusted_share1'] = round(np.true_divide(nonfaculty_final['careerarea_y'], nonfaculty_final['careerarea_x']) * 100, 1)
            top_skills_name.append(occ_2.iloc[0]['occupation_2'])

            # merge skill table
            career_table = career_table.merge(skill_df_year2, how='inner', on='jobid')
            career_table_year1 = career_table_year1.merge(skill_df_year1, how ='inner', on ='jobid')
            # career_table_year1['adjusted_share1'] = round(np.true_divide(nonfaculty_final['careerarea_y'], nonfaculty_final['careerarea_x']) * 100, 1)
            growth_table = pd.DataFrame(career_table_year1['skill_cluster_name'].value_counts())
            growth_table = growth_table.reset_index().rename(columns={'skill_cluster_name':'count_1', 'index':'skill_cluster_name'})
            growth_table['adjusted_share1'] = np.true_divide(growth_table['count_1'], total_year1)

            output = pd.DataFrame(career_table['skill_cluster_name'].value_counts())
            output = output.reset_index().rename(columns={'skill_cluster_name':'count', 'index':'skill_cluster_name'})
            growth_table = growth_table.merge(output, how = 'inner', on = 'skill_cluster_name')
            # print(growth_table)
            # print(growth_table)
            growth_table['adjusted_share2'] = np.true_divide(growth_table['count'], total_year2)
            print(growth_table)
            growth_table['growth'] = round(np.true_divide(growth_table['adjusted_share2']-growth_table['adjusted_share1'], growth_table['adjusted_share1']) * 100, 2)
            growth_table_filtered = growth_table[['skill_cluster_name', 'growth']]
            growth_table_filtered = growth_table_filtered[growth_table_filtered ['growth'] != float("inf")]
            growth_table_filtered = growth_table_filtered.sort_values(by ='growth', ascending = False)
            print(growth_table)
            growth_occ = []
            growth_occ.append(growth_table_filtered[:10].values.tolist())
            growth += growth_occ

            top_skills = []
            top_skills.append(output[:10].values.tolist())
            occupation_top_skills += top_skills
        return render_template("career_breakdown_result.html", career_top_occupation = career_top_occupation, requestedYears = requestedYears, requestedInstitution = requestedInstitution, careers = careers, occupation_top_skills = occupation_top_skills, top_skills_name = top_skills_name, growth = growth)

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

@app.route('/exploration_tool', methods = ["GET", "Post"])
def exploration_tool():
    if request.method == "GET":
        category = ['Career Area', 'Occupation', 'IPEDS Institution Name', 'Year', 'Metropolitan Statistical Area', 'Institution Type', 'Faculty']
        return render_template("exploration_tool.html", category = category, year_range = year_range, careerareas = careerareas, institutionType = institutionType, job_status = job_status)
    else:
        requestedCategory = request.form.getlist('category_value')
        requestedCareers = request.form.getlist('careerareas')
        requestedYear = request.form.getlist('year')
        requestedInstitution = request.form.getlist('institutionType')
        requestedFaculty = request.form.getlist('job_status')
        return render_template("exploration_tool_2.html", requestedCategory = requestedCategory)

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
