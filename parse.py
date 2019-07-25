import psycopg2
from collections import OrderedDict
from query import *
from fieldValues import *
from occupations import occupations
from nsfFields import *

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

def makeYearsMain(year):
    if (year==[]):
        return "true"
    result = "("
    for i in range(0,len(year)-1):
        result+= "maintable.year = "+year[i]+" or "
    result += " maintable.year = "+ year[len(year)-1]+" ) "
    return result

def makeStrings(list):
    if (list==[]):
        return "true"
    result = []
    for i in range(0,len(list)):
        result.append(list[i])
    return result

def getInstitutionDummy(institution):
    if (institution == 'All Higher Education'):
        return "true "
    if (institution == 'R1 Universities'):
        return "isresearch1institution = 1"
    if (institution == '4-year Institutions'):
        return "fouryear = 1"
    if (institution == '2-year Institutions'):
        return "twoyear = 1"

def getInstitutionType(institution):
    if (institution == 'All Higher Education'):
        return "true "
    if (institution == 'R1 Universities'):
        return "isresearch1institution"
    if (institution == '4-year Institutions'):
        return "fouryear"
    if (institution == '2-year Institutions'):
        return "twoyear"

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
