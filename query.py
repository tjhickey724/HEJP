import psycopg2
from collections import OrderedDict
from query import *
from fieldValues import *
from occupations import occupations
from nsfFields import *
from parse import *

# def queryphdShare(year, institution):
#     queryphdShare = "SELECT careerarea, count(careerarea) FROM "
#     queryphdShare += commonQueryPhd(year, institution)
#     queryphdShare += "GROUP BY careerArea "
#     queryphdShare += "ORDER BY COUNT(careerArea) DESC "
#     return queryphdShare
#
# def queryphdJob(year, institution):
#     queryphdJob = "SELECT occupation, count(occupation) FROM "
#     queryphdJob += commonQueryPhd(year, institution)
#     queryphdJob += "GROUP BY occupation "
#     queryphdJob += "ORDER BY COUNT(occupation) DESC "
#     return queryphdJob
def query_top_skill(year):
    query_top_skill = "SELECT jobid, year, skill_cluster_name From skilltable "
    query_top_skill += "WHERE year = " + year
    query_top_skill += "AND skill_cluster_name NOT LIKE 'nan' "
    return query_top_skill

def queryMentalHealth(year, institution):
    queryMentalHealth = "SELECT skill_cluster_name, maintable.year, fouryear, careerarea "
    queryMentalHealth += "FROM maintable "
    queryMentalHealth += "INNER JOIN skilltable on maintable.jobid = skilltable.jobid "
    queryMentalHealth += "WHERE skill_cluster_name ILIKE '%Mental and Behavior%' "
    queryMentalHealth += "AND " + makeYearsMain(year)
    queryMentalHealth += "AND " + getInstitutionDummy(institution)
    queryMentalHealth += "AND careerarea NOT LIKE 'na' "
    return queryMentalHealth

def commonQueryPhd(year, institution):
    queryphd = "SELECT maintable.jobid, faculty, maintable.year, fouryear, minimumedurequirements, "
    queryphd += "careerarea, occupation, jobtitle, ipedsinstitutionname "
    queryphd += "From maintable "
    queryphd += "INNER JOIN dummytable on maintable.jobid = dummytable.jobid "
    queryphd += "WHERE faculty = 0 "
    queryphd += "AND " + getInstitutionDummy(institution)
    queryphd += "AND minimumedurequirements = 21 "
    queryphd += "AND " + makeYearsMain(year)
    queryphd += "AND (careerarea NOT ILIKE '%Health Care including Nursing%' AND careerarea NOT LIKE 'na') "
    queryphd += "AND careerarea NOT ILIKE '%attorney%' "
    queryphd += "AND occupation NOT ILIKE '%attorney%' "
    queryphd += "AND jobtitle NOT ILIKE '%attorney%' "
    queryphd += "AND jobtitle NOT ILIKE '%title ix%' "
    queryphd += "AND jobtitle NOT ILIKE '%director of advancement%' "
    queryphd += "AND jobtitle NOT ILIKE '%finance manager%' "
    queryphd += "AND jobtitle NOT ILIKE '%financial manager%' "
    queryphd += "AND occupation NOT ILIKE '%financial manager%' "
    queryphd += "AND careerarea NOT ILIKE '%financial manager%' "
    queryphd += "AND ipedsinstitutionname NOT ILIKE '%law%' "
    queryphd += "AND ipedsinstitutionname NOT ILIKE '%medical%' "
    return queryphd

def queryCareer(years, institution):
    queryCareer = "SELECT year, Count(skill_cluster_name), skill_cluster_name from "
    queryCareer += "(SELECT occupation, " + getInstitutionType(institution) + ", maintable.year,  "
    queryCareer += "skillname, is_specialized_skill, is_software_skill, skill_cluster_name "
    queryCareer += "FROM maintable "
    queryCareer += "INNER JOIN skilltable on maintable.jobid = skilltable.jobid "
    queryCareer += "WHERE occupation LIKE 'Career Counselor' "
    queryCareer += "AND " + getInstitutionDummy(institution) + " "
    queryCareer += "AND " + makeYearsMain(years) + " "") As selected "
    queryCareer += "GROUP BY year, skill_cluster_name "
    queryCareer += "ORDER BY COUNT(skill_cluster_name) DESC"
    return queryCareer

def queryNonFaculty(years, institution):
    queryNonFaculty = "SELECT dummytable.year," + getInstitutionType(institution) + ", careerarea, faculty, postdoctoral, public, private "
    queryNonFaculty += "FROM maintable "
    queryNonFaculty += "Inner join dummytable on maintable.jobid = dummytable.jobid "
    queryNonFaculty += "WHERE faculty = 0"
    queryNonFaculty += "AND postdoctoral != 1"
    queryNonFaculty += "AND careerarea NOT ILIKE 'na' "
    queryNonFaculty += "AND " + makeYears(years) + " "
    queryNonFaculty += "AND " + getInstitutionDummy(institution)
    return queryNonFaculty

def queryScienceOpening(requestedYears):
    queryScienceOpening = "SELECT dummytable.year, isresearch1institution, ipedssectorname, fouryear, twoyear, "
    queryScienceOpening += "biologicalandbiomedicalsciences, chemistry, computerandinformationsciences, "
    queryScienceOpening += "geosciencesatmosphericandoceansc, mathematicsandstatistics, physicsandastronomy, "
    queryScienceOpening += "healthsciences,numberofdetailedfieldsofstudy,faculty,postdoctoral, tenured, "
    queryScienceOpening += "tenured_track, contingent "
    queryScienceOpening += "FROM maintable "
    queryScienceOpening += "INNER JOIN dummytable on maintable.jobid = dummytable.jobid "
    queryScienceOpening += "WHERE postdoctoral != 1 "
    queryScienceOpening += "AND faculty = 1 "
    queryScienceOpening += "AND (numberofdetailedfieldsofstudy > 2 OR healthsciences != 1) "
    queryScienceOpening += "AND " + makeYears(requestedYears) + " "
    queryScienceOpening += "AND (ipedssectorname NOT ILIKE 'nan' OR ipedssectorname NOT ILIKE '%Sector unknown (not active%') "
    return queryScienceOpening

def queryAllFaculty (requestedYears):
    queryAllFaculty = "SELECT maintable.year, ipedssectorname, "
    queryAllFaculty += "isresearch1institution, "
    queryAllFaculty += "postdoctoral, faculty, healthsciences, "
    queryAllFaculty += "numberofdetailedfieldsofstudy, contingent, fulltimecontingent, parttimecontingent, "
    queryAllFaculty += "tenured, tenured_track, fouryear, twoyear, tenureline "
    queryAllFaculty += "FROM maintable "
    queryAllFaculty += "INNER JOIN dummytable on maintable.jobid = dummytable.jobid "
    queryAllFaculty += "WHERE postdoctoral != 1 AND faculty = 1 "
    queryAllFaculty += "AND (numberofdetailedfieldsofstudy > 2 OR healthsciences != 1) "
    queryAllFaculty += "AND "+ makeYears(requestedYears)
    queryAllFaculty += "AND (ipedssectorname NOT ILIKE '%nan%' AND ipedssectorname NOT ILIKE '%Sector unknown (not active%' )"
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

# queries: NSF Growth
def queryNSFGrowth(f, requestedYears):
    queryNSFGrowth = "SELECT dummytable.year, " + makeFields(f) + " "
    # queryNSFGrowth += makeFields(f)
    queryNSFGrowth += "FROM dummytable "
    queryNSFGrowth += "WHERE (dummytable.healthsciences = 0 OR dummytable.numberofdetailedfieldsofstudy > 1) "
    queryNSFGrowth += "AND dummytable.faculty = 1 "
    queryNSFGrowth += "AND " + makeYears(requestedYears)
    return queryNSFGrowth

# query: share of faculty vs non faculty
# include: health care including nursing and healthsciences faculty
def queryFaculty (requestedYears):
    queryfaculty = "SELECT dummytable.year,"
    queryfaculty += "maintable.isresearch1institution, dummytable.postdoctoral, "
    queryfaculty += "dummytable.faculty, maintable.twoyear, maintable.fouryear "
    queryfaculty += "FROM maintable  "
    queryfaculty += "INNER JOIN dummytable ON dummytable.jobid = maintable.jobid "
    queryfaculty += "WHERE dummytable.postdoctoral != 1 "
    # queryfaculty += "AND maintable.careerarea NOT ILIKE '%Health Care including Nursing%' "
    # queryfaculty += "AND (dummytable.numberofdetailedfieldsofstudy > 2 OR dummytable.healthsciences !=1) "
    queryfaculty += "And " + makeYears(requestedYears)
    return queryfaculty
