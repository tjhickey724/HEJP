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

def calculate_phdshare(phd_df):
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
    phdshare_final = [career_area, count]
    return phdshare_final

def calculate_topjob(phd_df, top_jobs):
    top_jobs_res = top_jobs.to_records(index = False).tolist()
    job_count = []
    job_name = []
    for i in range(0, len(top_jobs_res)):
        job_name.append(top_jobs_res[i][0])
        job_count.append(top_jobs_res[i][1])
    top_jobs_final = [job_name, job_count]
    return top_jobs_final

def calculate_topskills(phd_df, top_jobs, skill_table):
    job1 = []
    job2 = []
    job3 = []
    job4 = []
    job5 = []
    job6 = []
    job7 = []
    job8 = []
    job9 = []
    job10 = []
    for index, row in top_jobs.iterrows():
        temp = phd_df[phd_df['occupation'] == row['index']]
        temp = temp.merge(skill_table.drop(columns = 'year'), on ='jobid', how ='inner')
        top_skills = pd.DataFrame(temp['skill_cluster_name'].value_counts()).reset_index(
        ).rename(columns={'skill_cluster_name':'count', 'index':'skill_cluster_name'})[:10]
        job1.append(list(top_skills['skill_cluster_name'])[0])
        job2.append(list(top_skills['skill_cluster_name'])[1])
        job3.append(list(top_skills['skill_cluster_name'])[2])
        job4.append(list(top_skills['skill_cluster_name'])[3])
        job5.append(list(top_skills['skill_cluster_name'])[4])
        job6.append(list(top_skills['skill_cluster_name'])[5])
        job7.append(list(top_skills['skill_cluster_name'])[6])
        job8.append(list(top_skills['skill_cluster_name'])[7])
        job9.append(list(top_skills['skill_cluster_name'])[8])
        job10.append(list(top_skills['skill_cluster_name'])[9])
    top_skills_final = [job1, job2, job3, job4, job5, job6, job7, job8, job9, job10]
    return top_skills_final

def calculate_allfaculty(faculty_status, queryfaculty_df):
    institution_type_df = queryfaculty_df[queryfaculty_df[faculty_status] == 1]
    # calculate R1 growth
    institution_type_R1 = list(institution_type_df[institution_type_df['isresearch1institution'] == 1].sort_values('year').groupby('year').apply(lambda x: x.year).value_counts())
    institution_type_R1.append(round(np.true_divide(institution_type_R1[0]-institution_type_R1[1], institution_type_R1[1]) * 100, 2))
    # calculate four year growth
    institution_type_fouryear = list(institution_type_df[institution_type_df['fouryear'] == 1].groupby('year').apply(lambda x: x.year).value_counts())
    institution_type_fouryear.append(round(np.true_divide(institution_type_fouryear[0]-institution_type_fouryear[1], institution_type_fouryear[1]) * 100, 2))
    # calculate two year growth
    institution_type_twoyear = list(institution_type_df[institution_type_df['twoyear'] == 1].groupby('year').apply(lambda x: x.year).value_counts())
    institution_type_twoyear.append(round(np.true_divide(institution_type_twoyear[0]-institution_type_twoyear[1], institution_type_twoyear[1]) * 100, 2))
    # calculate all higher growth
    institution_type_all = list(institution_type_df.groupby('year').apply(lambda x: x.year).value_counts())
    institution_type_all.append(round(np.true_divide(institution_type_all[0]-institution_type_all[1], institution_type_all[1]) * 100, 2))
    institution_type_result = [tuple(list(institution_type_R1)), tuple(list(institution_type_fouryear)), tuple(list(institution_type_twoyear)), tuple(list(institution_type_all))]
    return institution_type_result

def calculate_faculty_share(faculty_df, institution, requestedYears):
    if institution != "All Higher Education":
       institution_type = getInstitutionType(institution)
       institution_df = pd.DataFrame(faculty_df[faculty_df[institution_type] == 1])
       institution_year1 = institution_df[institution_df['year'] == int(requestedYears[0])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_1'})
       institution_year2 = institution_df[institution_df['year'] == int(requestedYears[1])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_2'})
       institution_final = institution_year1.merge(institution_year2, on = 'index', how = 'inner')
       institution_final_list = [list(institution_final['count_1']),list(institution_final['count_2'])]
       return institution_final_list
    else:
       institution_df = pd.DataFrame(faculty_df.drop(columns = ['isresearch1institution', 'fouryear', 'twoyear']))
       institution_year1 = institution_df[institution_df['year'] == int(requestedYears[0])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_1'})
       institution_year2 = institution_df[institution_df['year'] == int(requestedYears[1])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_2'})
       institution_final = institution_year1.merge(institution_year2, on = 'index', how = 'inner')
       institution_final_list = [list(institution_final['count_1']),list(institution_final['count_2'])]
       return institution_final_list

def calculate_science_opening(science_df, science, requestedYears):
    science_field = makeFields([science])
    science_field = science_field[0: len(science_field)-1]
    sub_science_df = science_df[[science_field, 'year', 'tenure_line', 'contingent']]
    sub_science_df = sub_science_df[sub_science_df[science_field] == 1].drop(columns = science_field)
    # breakdown by year
    breakdown_year1 = sub_science_df[sub_science_df['year'] == int(requestedYears[0])].drop(columns = 'year')
    breakdown_year2 = sub_science_df[sub_science_df['year'] == int(requestedYears[1])].drop(columns = 'year')
    # tenureline for different years
    breakdown_year1_total = breakdown_year1.sum().reset_index().rename(columns = {0: 'count_1'})
    breakdown_year1_total.loc[2] = ['total', sum(breakdown_year1_total['count_1'])]
    breakdown_year2_total = breakdown_year2.sum().reset_index().rename(columns = {0: 'count_2'})
    breakdown_year2_total.loc[2] = ['total', sum(breakdown_year2_total['count_2'])]
    breakdown_final = breakdown_year1_total.merge(breakdown_year2_total, on = 'index', how = 'inner')
    print(breakdown_final)
    # contingent for different years
    # breakdown_year2_tenureline = pd.DataFrame(breakdown_year2[breakdown_year2['tenure_line'] == 1].sum())
    # breakdown_year2_contingent = pd.DataFrame(breakdown_year2[breakdown_year2['contingent'] == 1].sum())

    return science_opening_list
