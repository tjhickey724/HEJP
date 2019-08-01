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
from phd_distribution import *

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
    top_skills_final = []
    for index, row in top_jobs.iterrows():
        temp = phd_df[phd_df['occupation'] == row['index']]
        temp = temp.merge(skill_table.drop(columns = 'year'), on ='jobid', how ='inner')
        top_skills = pd.DataFrame(temp['skill_cluster_name'].value_counts()).reset_index(
        ).rename(columns={'skill_cluster_name':'count', 'index':'skill_cluster_name'})[:10]
        top_skills_final.append(list(top_skills['skill_cluster_name']))
    return top_skills_final
