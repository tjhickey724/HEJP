import psycopg2
from collections import OrderedDict
from query import *
from fieldValues import *
from occupations import occupations
from nsfFields import *
from parse import *

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

# queries: NSF Growth
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

# query: share of faculty vs non faculty
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
