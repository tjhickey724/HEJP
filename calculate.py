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
    else:
       institution_df = pd.DataFrame(faculty_df.drop(columns = ['isresearch1institution', 'fouryear', 'twoyear']))

    postdoc_df = institution_df[institution_df['postdoctoral'] == 1].drop(columns = 'faculty')
    postdoc_df = postdoc_df.groupby('year').apply(lambda x: x.year).value_counts().reset_index().rename(columns = {'year':'postdoc_count', 'index': 'year'})
    institution_df = institution_df[institution_df['postdoctoral'] != 1].drop(columns = 'postdoctoral')
    institution_year1 = institution_df[institution_df['year'] == int(requestedYears[0])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_1'})
    institution_year2 = institution_df[institution_df['year'] == int(requestedYears[1])].groupby('faculty').apply(lambda x: x.faculty).value_counts().reset_index().rename(columns={'faculty':'count_2'})
    institution_final = institution_year1.merge(institution_year2, on = 'index', how = 'inner')
    institution_final.loc[3] = ['2', postdoc_df.iloc[1, 1], postdoc_df.iloc[0, 1]]
    institution_final['share_1'] = round(np.true_divide(institution_final['count_1'], sum(institution_final['count_1'])) * 100, 1)
    institution_final['share_2'] = round(np.true_divide(institution_final['count_2'], sum(institution_final['count_2'])) * 100, 1)
    institution_final_list = [list(institution_final['count_1']),list(institution_final['count_2']), list(institution_final['share_1']), list(institution_final['share_2'])]
    return institution_final_list

def calculate_merge_nsfGrowth(breakdown_year1, breakdown_year2, requestedFields):
    private_df = pd.DataFrame(columns = ['field', 'type', 'count_1', 'count_2', 'growth'])
    public_df = pd.DataFrame(columns = ['field', 'type', 'count_1', 'count_2', 'growth'])
    total_df = pd.DataFrame(columns = ['field', 'type', 'count_1', 'count_2', 'growth'])
    for field in requestedFields:
        field_df = calculate_nsfGrowth(breakdown_year1, breakdown_year2, field)
        private_df.loc[len(private_df)] = field_df.iloc[0]
        public_df.loc[len(public_df)] = field_df.iloc[1]
        total_df.loc[len(total_df)] = field_df.iloc[2]
    # sort values
    private_df = private_df.sort_values(by=['growth'], ascending=False)
    public_df = public_df.sort_values(by=['growth'], ascending=False)
    total_df = total_df.sort_values(by=['growth'], ascending=False)
    print(private_df)
    print(public_df)
    print(total_df)

    if len(requestedFields) >= 10:
        top_list = total_df[['field', 'growth']][:10]
        top_growth = get_top_growth (top_list, private_df, public_df)
    else:
        top_list = total_df[['field', 'growth']]
        top_growth = get_top_growth (top_list, private_df, public_df)

    private_name = add_percent_to_name(private_df, 'field', 'growth')
    public_name = add_percent_to_name(public_df, 'field', 'growth')
    total_name = add_percent_to_name(total_df, 'field', 'growth')
    private_final_list = [private_name, list(private_df['count_1']), list(private_df['count_2'])]
    public_final_list = [public_name, list(public_df['count_1']), list(public_df['count_2'])]
    total_final_list = [total_name, list(total_df['count_1']), list(total_df['count_2'])]
    final_list = [private_final_list, public_final_list, total_final_list, top_growth]
    return final_list

#get the element with top growth rate
def get_top_growth(top_list, private_df, public_df):
    private_growth = private_df[['field', 'growth']]
    top_list = top_list.merge(private_growth, on = 'field', how = 'inner')

    private_relative_rank = top_list[['field', 'growth_y']].sort_values(by=['growth_y'], ascending=False).reset_index()
    private_relative_rank.index = np.arange(1, len(private_relative_rank)+1)
    private_relative_rank = private_relative_rank.drop(columns=['index', 'growth_y'])

    private_relative_rank['private_rank'] = private_relative_rank.index
    top_list = top_list.merge(private_relative_rank, on='field', how='inner')
    # private_growth = private_growth.sort_values(by=['growth'], ascending=False).reset_index().shift()[1:].drop(columns='index')
    # private_growth['rank_private'] = private_growth.index
    public_growth = public_df[['field', 'growth']]
    top_list = top_list.merge(public_growth, on = 'field', how = 'inner')
    public_relative_rank = top_list[['field', 'growth']].sort_values(by=['growth'], ascending=False).reset_index()
    public_relative_rank.index = np.arange(1, len(public_relative_rank)+1)
    public_relative_rank = public_relative_rank.drop(columns=['index', 'growth'])
    public_relative_rank['public_rank'] = public_relative_rank.index
    top_list = top_list.merge(public_relative_rank, on='field', how='inner')

    print(top_list)
    # public_growth = public_growth.sort_values(by=['growth'], ascending=False).reset_index().shift()[1:].drop(columns='index')
    # public_growth['rank_public'] = public_growth.index

    top_list = top_list.merge(public_growth, on = 'field', how = 'inner')
    top_list_final = top_list.values.tolist()

    return top_list_final

# append the percent growth to the name: nsf field
def add_percent_to_name(df, index_1, index_2):
    field_name = list(df[index_1])
    for i in range(0, len(df[index_2])):
        field_name[i] += '  (' + str(list(df[index_2])[i]) + '%)'
    return field_name

def calculate_nsfGrowth(breakdown_year1, breakdown_year2, field):
    # breakdown by public
    selected_field = makeFields([field])
    selected_field = selected_field[0:len(selected_field)-1]
    selected_field_year1 = breakdown_year1[[selected_field, 'private', 'public']]
    selected_field_year1 = selected_field_year1[selected_field_year1[selected_field] == 1].drop(columns = selected_field)
    count_year1 = selected_field_year1.shape[0]

    selected_field_year1 = selected_field_year1.sum().reset_index().rename(columns= {0: 'count_1'})
    selected_field_year1.loc[2] = ['total', count_year1]

    selected_field_year2 = breakdown_year2[[selected_field, 'private', 'public']]
    selected_field_year2 = selected_field_year2[selected_field_year2[selected_field] == 1].drop(columns = selected_field)
    count_year2 = selected_field_year2.shape[0]

    selected_field_year2 = selected_field_year2.sum().reset_index().rename(columns= {0: 'count_2'})
    selected_field_year2.loc[2] = ['total', count_year2]
    selected_field_final = selected_field_year1.merge(selected_field_year2, on = 'index', how = 'inner')
    selected_field_final = selected_field_final.rename(columns = {'index': 'type'})
    selected_field_final['growth'] = round(np.true_divide(selected_field_final['count_2']-selected_field_final['count_1'],  selected_field_final['count_1']) * 100, 1)
    selected_field_final.insert(0, "field", [field, field, field])

    return selected_field_final

def calculate_science_opening(science_df, science, requestedYears):
    science_field = makeFields([science])
    science_field = science_field[0: len(science_field)-1]
    sub_science_df = science_df[[science_field, 'year', 'tenure_line', 'contingent']]
    sub_science_df = sub_science_df[sub_science_df[science_field] == 1].drop(columns = science_field)
    # breakdown by year
    breakdown_year1 = sub_science_df[sub_science_df['year'] == int(requestedYears[0])].drop(columns = 'year')
    count_row_1 = breakdown_year1.shape[0]
    breakdown_year2 = sub_science_df[sub_science_df['year'] == int(requestedYears[1])].drop(columns = 'year')
    count_row_2 = breakdown_year2.shape[0]

    breakdown_year1_total = breakdown_year1.sum().reset_index().rename(columns = {0: 'count_1'})
    breakdown_year1_total.loc[2] = ['total', count_row_1]
    breakdown_year1_total.loc[3] = ['tenure_share', round(np.true_divide(breakdown_year1_total.iloc[0, 1], breakdown_year1_total.iloc[2, 1]) * 100, 1)]
    breakdown_year1_total.loc[4] = ['contingent_share', round(np.true_divide(breakdown_year1_total.iloc[1, 1], breakdown_year1_total.iloc[2, 1]) * 100, 1)]

    breakdown_year2_total = breakdown_year2.sum().reset_index().rename(columns = {0: 'count_2'})
    breakdown_year2_total.loc[2] = ['total', count_row_2]
    breakdown_year2_total.loc[3] = ['tenure_share', round(np.true_divide(breakdown_year2_total.iloc[0, 1], breakdown_year2_total.iloc[2, 1]) * 100, 1)]
    breakdown_year2_total.loc[4] = ['contingent_share', round(np.true_divide(breakdown_year2_total.iloc[1, 1], breakdown_year2_total.iloc[2, 1]) * 100, 1)]
    breakdown_final = breakdown_year1_total.merge(breakdown_year2_total, on = 'index', how = 'inner')
    breakdown_total = []
    breakdown_total.append(breakdown_final['count_1'][2])
    breakdown_total.append(breakdown_final['count_2'][2])
    tenure_share = breakdown_final.iloc[3, 1:3]
    contingent_share = breakdown_final.iloc[4, 1:3]
    science_opening_list = [breakdown_total, list(tenure_share), list(contingent_share)]
    # print(science_opening_list)
    return science_opening_list
