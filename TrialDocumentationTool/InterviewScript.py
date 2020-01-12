"""
Purpose: To document and resurface lesssons
Inputs: Lesson compendium JSON file, lesson documentation template, lesson search template
Outputs: Lesson compendium JSON file(Updated), relevant lesson dataframe
Date: 2019-05-06
Author: Daniel Min
"""


# Import packages

import json
import glob
import xlrd
import pprint
import pandas as pd
import numpy as np
import pprint
import nltk 
from nltk.corpus import wordnet 
from fuzzywuzzy import fuzz

# Define inputs
## Update this section and the templates as the lesson learned data changes

AttributesFields = ["Patient_Profile", "Symptoms", "Specialty", "Therapy", "Trial_Time", "Other"]
LesssonsFields = ["Lesson_Name", "Description", "Date", "Warning_Level", "Recommendation"]
TrialFields = ["Trial_Name", "Trial_Start_Date", "Study_Manager_Name", "Vant_Name"]

AllFields = AttributesFields + LesssonsFields + TrialFields

# Functions for reading the templates
def LowerCase(list1):
    """
    Turn all strings in the list into a lower case
    """
    return [word.lower() for word in list1]

def ReduceDataframe(df, field):
    """
    For a given row, combine all string across all columns into one list and save it as a column
    """
    Dict = {}
    for row in df.iterrows():
        AllKeyWords = []
        index, data = row
        if index in field:
            data = data.dropna()
            List = [words for segments in data.tolist() for words in segments.split()]
            AllKeyWords += (List)
            Dict[index] = AllKeyWords
    
    return Dict

def LessonTrialReadSheets(field, df, path):
    """
    Read lesson and trial information for each lesson in the excel tempalte
    """
    ResultDict = {}
    ResultDf = pd.read_excel(path, df, skiprows = 3, usecols =[1,2])
    for index, row in ResultDf.iterrows():
                if row['Field'] in field:
                    ResultDict[row['Field']] = str(row['Value'])
    
    return ResultDict


def AttributeReadSheets(field, df, path, pull):
    """
    Read attribute information for each lesson in the excel tempalte
    """
    ResultDict = {}
    ResultDf = pd.read_excel(path, df, skiprows = 3).drop(["Unnamed: 0"], axis=1)
    ResultDf = ResultDf.set_index(ResultDf["Field"]).drop("Field", axis =1)
    
    ResultDict = ReduceDataframe(ResultDf, field)
    
    return ResultDict

    # Import excel lesson documentation template
## Input: lesson documentaiton template
## Output: dictionary with the information on the lesson that requires documentation

path = "./"
ExcelLogPath = glob.glob(path+'Lesson documentation template.xlsx')[0]
ExcelLesson = xlrd.open_workbook(r''+ExcelLogPath, on_demand=True)
AllLessons = []

for lessons in ExcelLesson.sheet_names():
    if lessons != "Instructions":
        if lessons == "Trial":
            DictTrial = LessonTrialReadSheets(TrialFields, lessons, ExcelLogPath)
        else:
            # Lessons
            DictLesson = LessonTrialReadSheets(LesssonsFields, lessons, ExcelLogPath)
            
            # Attributes
            DictAttributes = AttributeReadSheets(AttributesFields, lessons, ExcelLogPath, "")
            
            DictEntry = DictLesson
            DictEntry["Attributes"] = DictAttributes
            DictEntry["Trial"] = DictTrial
            AllLessons.append(DictEntry)

print(AllLessons)


# Read the exisitng lesson in the JSON file and add the new ones from the excel template
## Input and output: lesson compendium JSON file

with open("Lesson compendium.json", "r") as jsonFile:
    data = json.load(jsonFile)
    data["Lessons"] += AllLessons
    
with open("Lesson compendium.json", "w") as jsonFile:
    json.dump(data, jsonFile)


    # Pull data from the search template
## Input: excel search tempalte
## Output: dictionary with search specification

path = "./"
ExcelSearchPath = glob.glob(path+'Lesson search template.xlsx')[0]
ExcelSearch = xlrd.open_workbook(r''+ExcelSearchPath, on_demand=True)

for tab in ExcelSearch.sheet_names():
    if tab != "Instructions":
        DictSearch = AttributeReadSheets(AllFields, tab, ExcelSearchPath, "")

print(DictSearch)



# Functions for identifying synonyms and ranking the relevance of the lessons

def FindSynonym (dictionary, key, Finlist):
    """
    Find all synonyms for each word
    """
    for word in dictionary[key]:
        synonyms = [] 
        for syn in wordnet.synsets(word): 
            for l in syn.lemmas(): 
                synonyms.append(l.name()) 
        synonyms = list(set(synonyms))
        Finlist = dict(Finlist, **{word: synonyms})
    
    return Finlist

def EvaluateMatch (field, synDict, lesson):
    """
    Give a score for each word in the specification from the excel template file
    """
    AllScore = 0
    for subField in lesson[field]:
        if subField in synDict:
            for word in synDict[subField]:
                TrackScore = 0
                for syn in synDict[subField][word]:
                    if field == "Trial":
                        LessonWords = lesson[field][subField].split(" ")
                    elif field == "Attributes":
                        LessonWords = lesson[field][subField]
                    for lessonWord in LessonWords:
                        Score = fuzz.ratio(syn,lessonWord)
                        if fuzz.ratio(syn,lessonWord) > 80 and TrackScore == 0:
                            TrackScore += 1         
                AllScore += TrackScore
    return(AllScore)



    # Pull synonyms from the search keywords
## Input: dictionary with search specification
## Output: dictionary with keywords AND their synonyms

DictSearchSyn = DictSearch

for key in DictSearchSyn:
    KeySyn = {}
    if key != "Warning_Level":
        KeySyn = FindSynonym (DictSearchSyn, key, KeySyn)
    else:
        KeySyn = DictSearchSyn[key]
    DictSearchSyn[key] = KeySyn
   
print(DictSearchSyn)



# Rank and sort the lessons

with open("Lesson compendium.json", "r") as jsonFile:
    data = json.load(jsonFile)
    
ScoreData = []
for lesson in data["Lessons"]:
    AllScore = 0
    for field in lesson:
        if field == "Trial" or field == "Attributes":
            Score = EvaluateMatch (field, DictSearchSyn, lesson)
            AllScore += Score
        elif field == "Warning_Level":
            if DictSearchSyn[field][0] == lesson[field]:
                AllScore += 1      
    if AllScore > 0:
        ScoreData.append([lesson["Lesson_Name"], lesson["Description"], lesson["Warning_Level"], lesson["Recommendation"], AllScore ])


# Display lessons

from IPython.display import display
pd.options.display.max_rows
pd.set_option('display.max_colwidth', -1)

FinalOutput = pd.DataFrame(ScoreData, columns = ['Lesson Name',"Description", "Warning Level", "Recommendation", 'Relevance Score']) 
FinalOutput = FinalOutput.sort_values(by=['Relevance Score', 'Lesson Name'], ascending=False).reset_index(drop=True)
display(FinalOutput)

