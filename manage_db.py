#!/usr/bin/env python
#-*- coding: utf-8 -*-
# THOUVENIN Arthur athouvenin@outlook.fr
# 01/01/2020
########################

import csv
import datetime
import git
import json
import os
import pymongo
import random
import re
import requests
import sys
import time
import zipfile
from IPython.display import clear_output
from sklearn.feature_extraction.text import TfidfVectorizer # Allows transformations of string in number
from sklearn.linear_model import LogisticRegressionCV # Allows to use the Logistic Regression from Scikit-Learn (https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
from sklearn.model_selection import train_test_split
from sklearn import metrics
import pickle
import pandas
from extract import searchPOST

tmp_directory="./TMP/"

client=pymongo.MongoClient("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
db_lit=client.literature.ROR_testing
hitCount=0
pmidCount=0
TIMES=[]

def update_ror_json(rorapi_directory="ror-api/",update_directory="./update_dir/"): #### update ror.json based on ROR API's github
    """This function will pull an update from the ROR API's github and then update the ror.json file
    Description :
            This function is used to pull the ROR API's github and then extract in the corresponding directory the ror.json,
            corresponding to all ROR records.
    Args :
            rorapi_directory (string) : 
                    Directory name where the ROR API will be pulled from GitHub.
            update_directory (string) :
                    A path of the update directory.
    Return :
            No return
    """
    if not os.path.isdir(update_directory):
        os.mkdir(update_directory)
    if not os.path.isdir(update_directory+rorapi_directory):
        git.Git(update_directory).clone("https://github.com/ror-community/ror-api.git")
    g=git.cmd.Git(update_directory+rorapi_directory)
    g.pull()
    data_ROR_updates=[x[0].split("\\")[-1] for x in os.walk(update_directory+rorapi_directory+"rorapi/data")][1:]
    tmp=[]
    for date in data_ROR_updates:
        if "ror" in date:
            tmp.append(datetime.date(int(date.split("-")[1]),int(date.split("-")[2]),int(date.split("-")[3])))
    latest_update_f="ror-"+str(max(tmp))
    tmp=None
    data_ROR_updates=None
    with zipfile.ZipFile(update_directory+rorapi_directory+"rorapi/data/"+latest_update_f+"/ror.zip",'r') as zip_ref:
        zip_ref.extractall(update_directory)

def build_ROR_GRID_json(filename="dictio_C_c_ROR.json",update_directory="./update_dir/"): #### add city to ROR records thanks to GRID
    """ This function will add to all ROR records the corresponding city based on the GRID database
    Description :
            This function thanks to the file ror.json(data from ROR) and grid.csv(data from GRID).
            In the end all records will be saved in a list that ill be saved in the file gave as an argument.
    Args :
            filename (string) :
                    A name for the resulting file.
            update_directory (string) :
                    A path of the update directory.
    Return :
            No return
    """
    with open(update_directory+"ROR_GRID_notFound.tsv","a",encoding="utf-8") as f:
        f.write("ROR IDs\tGRID\n")

    with open(update_directory+"ror.json",'r',encoding="utf-8") as f:
        ROR=json.loads(f.read())
        f.close()

    url="https://www.grid.ac/downloads"
    grid_req=requests.get(url)
    url=re.findall(r'[^"]+ndownloader[^"]+',grid_req.text)[0]
    grid_req=requests.get(url,stream=True,allow_redirects=True)
    import io
    z = zipfile.ZipFile(io.BytesIO(grid_req.content))
    z.extract("grid.csv",path=update_directory)

    GRID={}
    with open(update_directory+"grid.csv","r",encoding="utf-8") as f:
        reader=csv.DictReader(f,delimiter=',',quotechar='"')
        for lines in reader:
            GRID[lines["ID"]]={
                "name":lines["Name"],
                "city":lines["City"],
                "state":lines["State"],
                "country":lines["Country"]}
        f.close()

    x=0
    dataset=[]
    TIMES=[]
    for org in ROR:
        try:
            start=time.time()
            x+=1
            print(org["id"])
            country=org["country"]["country_name"].replace(" ","_")
            del org["country"]
            grid_id=org["external_ids"]["GRID"]["preferred"]
            city=GRID[grid_id]["city"].replace(" ","_").replace(".","@")
            org["country"]=country
            org["city"]=city
            dataset.append(org)
            os.system('cls' if os.name == 'nt' else 'clear')
            clear_output(wait=True)
            end=time.time()
            TIMES.append(end-start)
            print("Number of RORs in ROR data : "+str(len(dataset)))
            print(str(x)+"/"+str(len(ROR)))
            print("Time estimated : "+str(datetime.timedelta(seconds=int(round(sum(TIMES)/len(TIMES),2)*(len(ROR)-x)))))
        except KeyError:
            with open(update_directory+"ROR_GRID_notFound.tsv","a",encoding="utf-8") as f:
                f.write(org["id"])
                f.write("\t")
                f.write(org["external_ids"]["GRID"]["preferred"])
                f.write("\n")
                f.close()
    with open(update_directory+filename,"w",encoding="utf-8") as f:
        json.dump(dataset,f,ensure_ascii=False)

def clean_name(ROR_ID,display=False): #### clean a ROR ID name
    """ This function will clean the name of ROR IDs
    Description :
            This function will update the ROR ID name if it follow this pattern : Institution (Germany). 
            If a country name appear in parenthesis in the name of the institution thus it means it is only the site of the institution.
            Therefore the correct name is the one without parenthesis and country name. However to be sure of the name if the name contains the city name
            or country name or "-" the function will return True to indicate it needs an human verification.
    Args :
            ROR_ID (string) :
                    The ROR ID to process.
            display (boolean) :
                    A boolean to indicate if the display is needed.
    Return :
            True if there is a need of an human verification.
            False if not.
    """
    ROR=db_lit.find_one({"id":ROR_ID})
    if " ("+ROR["country"].replace("_"," ")+")" in ROR["name"]:
        db_lit.update_one({"id":ROR["id"]},{"$set":{"name":ROR["name"].replace(" ("+ROR["country"].replace("_"," ")+")","")}})
    elif ROR["city"].replace("_"," ").replace("@",".") in ROR["name"] or ROR["country"].replace("_"," ") in ROR["name"] or "-" in ROR["name"]:
        if display:
            print("### Country or city in name ###")
            print("ID : "+ROR["id"])
            print("Name : \033[31m"+ROR["name"]+"\033[0m")
            print("CITY : "+ROR["city"])
            print("COUNTRY : "+ROR["country"])
            print('{"id":"'+ROR["id"]+'","name":"'+ROR["name"]+'","city":"'+ROR["city"]+'","country":"'+ROR["country"]+'"}')
            input()
        return True
    return False
        
def refresh_MongoDB(filename="dictio_C_c_ROR.json",update_directory="./update_dir/",collect=True,train=True): #### add new records in MongoDB collection
    """ This function will had new records to the MongoDB collection thanks to the json file pass as argument
    Description :
            The function will first load the json where ROR+GRID records has been stored, then for each new record, it will had it to the corresponding MongoDB collection
    Args :
        filename (string) :
                The name of the loading file
        update_directory (string) : 
                Path of the update directory where all files needed will be generated.
        collect (boolean) : 
                A boolean to indicate if you want to collect unique affiliations for the new ROR records.
        train (boolean) : 
                A boolean to indicate if you want to train the new ROR records with the unique affiliations collected.
    Return :
            refresh_MongoDB() (list) :
                    A list of strings which corresponds to new ROR IDs in the collection.
    """
    collection_size=100

    if not os.path.isfile(update_directory+"clean_names.tsv"):
        with open(update_directory+"clean_names.tsv",mode="w",encoding="utf-8") as f:
            f.write("ROR_ID\tName\tCity\tCountry\n")
            f.close()

    with open(update_directory+filename,"r",encoding="utf-8") as f:
        db=json.loads(f.read())
        f.close()
    
    new=0
    new_RORs=[]
    for ROR in db:
        if db_lit.find_one({"id":ROR["id"]})==None:
            new_RORs.append(ROR["id"])
            db_lit.insert_one(ROR)
            new+=1
            if clean_name(ROR["id"]):
                with open(update_directory+"clean_names.tsv",mode="a",encoding="utf-8") as f:
                    f.write("\t".join([ROR["id"],ROR["name"],ROR["city"],ROR["country"]]))
                    f.write("\n")
        os.system('cls' if os.name == 'nt' else 'clear')
        clear_output(wait=True)
        print("New oraganizations registered : "+str(new))
    
    if collect:
        for ROR in new_RORs:
            ORG=db_lit.find_one({"id":ROR})
            req=build_request(ORG["name"],ORG["city"],ORG["country"])
            get_aff_requested(req,size=collection_size)
    if train:
        now=datetime.datetime.now()
        train_all(new=True,date=now.strftime("%Y-%m-%d"))
    return new_RORs

def update_collection(rorapi_directory="ror-api/",filename="dictio_C_c_ROR.json",update_directory="./update_dir/",collect=True,train=True,clean=False): #### update the ROR collection thanks to GRID
    """This function will update the collection with all new RORs.
    Description :
            This function will pull an update from the ROR API's github, then match cities from GRID,
            update the MongoDB collection, makes searches for 'new' institutions in the collection and thus fill with unique affiliations there datasets.
            In the end if there are enough data, the algorithm will train the new models.
    Args :
            rorapi_directory (string) : 
                    Name of the ROR API directory used to pull from GitHub.
            filename (string) : 
                    Name of the file resulting from the match of cities from GRID.
            update_directory (string) : 
                    Path of the update directory where all files needed will be generated.
            collect (boolean) : 
                    A boolean to indicate if you want to collect unique affiliations for the new ROR records.
            train (boolean) : 
                    A boolean to indicate if you want to train the new ROR records with the unique affiliations collected.
            clean (boolean) : 
                    A boolean to indicate if you want to clean your machine from all the files used during the process.
    Return :
            NEW (list) :
                    A list of strings which corresponds to new ROR IDs in the collection.
    """

    update_ror_json(rorapi_directory=rorapi_directory,update_directory=update_directory)
    build_ROR_GRID_json(filename=filename,update_directory=update_directory)
    NEW = refresh_MongoDB(filename=filename,update_directory=update_directory,collect=collect,train=train)
    if clean:
        import shutil
        shutil.rmtree(update_directory)
    return NEW

def get_stats(types=False,status=False,country=False,city=False,list_aff=False,model=False,save=False): #### get stats from mongodb collection
    """This function provides some statistics from the MongoDB collection
    Description :
            This function use multiple sub-functions to return some statistics from the MongoDB collection, it returns those results and it is possible to save those in a directory
    Args :
            types (boolean) :
                    Ask stats about organizations types
            status (boolean) :
                    Ask stats about organizations status
            country (boolean) :
                    Ask stats about organizations countries
            city (boolean) :
                    Ask stats about organizations cities
            list_aff (boolean) :
                    Ask stats about organizations affiliations caught by exact match and store in the MongoDB collection
            model (boolean) :
                    Ask stats about organizations trained models such as different scores
            save (boolean):
                    use to know if sub function needs to save results in a file
    Return :
            RESULT (list) :
                    A list of dictionary each one contains statistics from MongoDB
    """
    
    def get_types(save=save): #### gives stats about organization types
        """This function will go through MongoDB and return result about the "types" field
        Description :
                Currently there is 8 different types : Company, Education, Healthcare, Non-Profit, Other, Facility, Government, Archive in the collection.
                This function will go through the collection and get some statistics(number of organizations for each type) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                TYPES (dictionary) :
                        This dictionary will contains the number of organizations of each type in the following format :
                            {
                                "Company":2000,
                                "Education":300
                            }
        """
        TYPES={}
        all_types=db_lit.distinct("types")
        for typ in all_types:
            TYPES[typ]=db_lit.count({"types":typ})
        # all_RORs=db_lit.distinct("id")
        # for ROR in all_RORs:
        #     ROR_record=db_lit.find_one({"id":ROR},{"types":1})
        #     for typ in ROR_record["types"]:
        #         if typ in TYPES:
        #             TYPES[typ]+=1
        #         else:
        #             TYPES[typ]=1
        if save:
            with open("./statistics/typesMongoDB.csv","w") as f:
                for typ in TYPES:
                    f.write(typ)
                    f.write("\t")
                    f.write(str(TYPES[typ]))
                    f.write("\n")
                f.close()
        print("Types collected")
        return TYPES

    def get_status(save=save): #### gives stats about organization status
        """This function will go through MongoDB and return result about the "status" field
        Description :
                Currently there is only ine status in the collection : active
                This function will go through the collection and get some statistics(number of organizations for each status) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                STATUS (dictionary) :
                        This dictionary will contains the number of organizations with corresponding status in the following format :
                            {
                                "Active":45085
                            }
        """
        STATUS={}
        stat=db_lit.distinct("status")
        for st in stat:
            if st not in STATUS:
                STATUS[st]=db_lit.find({"status":st}).count()
        if save:
            with open("./statistics/statusMongoDB.csv","w") as f:
                for sta in STATUS:
                    f.write(sta)
                    f.write("\t")
                    f.write(str(STATUS[sta]))
                    f.write("\n")
                f.close()
        print("Status collected")
        return STATUS

    def get_country(save=save): #### gives stats about organization countries
        """This function will go through MongoDB and return result about the "country" field
        Description :
                This function will go through the collection and get some statistics (number of organizations for each country) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                COUNTRY (dictionary) :
                        This dictionary will contains the number of organizations for each country in the following format :
                            {
                                "United_States":45085,
                                "United_Kingdom":54126,
                                "Germany":5455
                            }
        """
        COUNTRY={}
        countries=db_lit.distinct("country")
        for country in countries:
            COUNTRY[country]=db_lit.find({"country":country}).count()
        if save:
            with open("./statistics/countryMongoDB.csv","w") as f:
                for cnty in COUNTRY:
                    f.write(cnty)
                    f.write("\t")
                    f.write(str(COUNTRY[cnty]))
                    f.write("\n")
                f.close()
        print("Countries collected")
        return COUNTRY
    
    def get_city(save=save): #### gives stats about organization cities
        """This function will go through MongoDB and return result about the "city" field
        Description :
                This function will go through the collection and get some statistics (number of organizations for each cities) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                CITY (dictionary) :
                        This dictionary will contains the number of organizations for each city in the following format :
                            {
                                "London":485,
                                "New_York":526,
                                "Caen":55
                            }
        """
        CITY={}
        duplicates=[]
        countries=db_lit.distinct("country")
        for country in countries:
            cities=db_lit.distinct("city",{"country":country})
            for city in cities:
                if city not in CITY:
                    CITY[city]=db_lit.find({"country":country,"city":city}).count()
                else:
                    duplicates.append(city)
                    del CITY[city]
        for duplicate in duplicates:
            countries=db_lit.distinct("country",{"city":duplicate})
            for country in countries:
                CITY[duplicate+"_"+country]=db_lit.find({"country":country,"city":duplicate}).count()
        if save:
            with open("./statistics/cityMongoDB.csv","w",encoding="utf-8") as f:
                for cit in CITY:
                    f.write(cit)
                    f.write("\t")
                    f.write(str(CITY[cit]))
                    f.write("\n")
                f.close()
        print("Cities collected")
        return CITY

    def get_list_aff(save=save): #### gives stats about organization affiliations
        """This function will go through MongoDB and return result about the "list_aff" field
        Description :
                This function will go through the collection and get some statistics (number of affiliations stored in the collection - training set) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                LIST_AFF (dictionary) :
                        This dictionary will contains the number of organizations for each city in the following format :
                            {
                                "with_affs":485,
                                "without_affs":526,
                                "distribution":{
                                    5460:2,
                                    56850:63,
                                    1:1000,
                                }
                            }
                        In the "distribution" dictionary the key corresponds to the length of the field in the collection and the value the frequency of the length in the collection
        """
        LIST_AFF={}
        LIST_AFF["distribution"]={}
        LIST_AFF["with_affs"]=db_lit.find({"list_aff":{"$exists":True}}).count()
        LIST_AFF["without_affs"]=db_lit.find({"id":{"$exists":True}}).count()-LIST_AFF["with_affs"]
        ROR_with_affs=db_lit.find({"list_aff":{"$exists":True}})
        for ROR in ROR_with_affs:
            length=len(ROR["list_aff"])
            if str(length) not in LIST_AFF["distribution"]:
                LIST_AFF["distribution"][str(length)]=1
            else:
                LIST_AFF["distribution"][str(length)]+=1
        if save:
            with open("./statistics/list_affMongoDB.csv","w") as f:
                f.write("with_affs\t")
                f.write(str(LIST_AFF["with_affs"]))
                f.write("\n")
                f.write("without_affs\t")
                f.write(str(LIST_AFF["without_affs"]))
                f.write("\n\n\n\n")
                for aff_len in LIST_AFF["distribution"]:
                    f.write(str(aff_len))
                    f.write("\t")
                    f.write(str(LIST_AFF["distribution"][str(aff_len)]))
                    f.write("\n")
                f.close()
        print("Affiliation lists collected")
        return LIST_AFF

    def get_model(save=save): #### gives stats about organization models
        """This function will go through MongoDB and return result about the "model" field
        Description :
                This function will go through the collection and get some statistics (different scores from the training of the model) and return those in a dictionary.
        Args :
                save (boolean) :
                        Use to know if the function need to save results in a file.
        Return :
                MODEL (dictionary) :
                        This dictionary will contains scores statistics in the following format :
                            {
                                'f1': {
                                    'average': 97.93,
                                    'maximum': 100.0, 
                                    'minimum': 26.43
                                },
                                'accuracy': {
                                    'average': 97.95, 
                                    'maximum': 100.0, 
                                    'minimum': 27.45
                                }, 
                                'precision': {
                                    'average': 97.98, 
                                    'maximum': 100.0, 
                                    'minimum': 26.26
                                },
                                'recall': {
                                    'average': 98.00, 
                                    'maximum': 100.0, 
                                    'minimum': 28.24
                                }
                            }
        """
        MODEL={}
        nb_models=0
        docs_model=db_lit.find({"model":{"$exists":True}},{"model":1})
        F1={
            "values":[],
            "name":"F1"}
        ACCURACY={
            "values":[],
            "name":"accuracy"}
        PRECISION={
            "values":[],
            "name":"precision"}
        RECALL={
            "values":[],
            "name":"recall"}
        for doc in docs_model:
            F1["values"].append(doc["model"]["f1_score"])
            ACCURACY["values"].append(doc["model"]["accuracy"])
            PRECISION["values"].append(doc["model"]["precision"])
            RECALL["values"].append(doc["model"]["recall"])
            nb_models+=1
        for score in [F1,ACCURACY,PRECISION,RECALL]:
            MIN=min(score["values"])
            MAX=max(score["values"])
            AVG=sum(score["values"])/len(score["values"])
            MODEL[score["name"]]={
                "average":AVG,
                "maximum":MAX,
                "minimum":MIN,
                "values":score["values"]}
        if save:
            with open("./statistics/modelMongoDB.csv","w") as f:
                f.write("Number of model trained\t")
                f.write(str(nb_models))
                f.write("\n")
                for score in MODEL:
                    f.write(score)
                    f.write("\nAverage\t")
                    f.write(str(MODEL[score]["average"]))
                    f.write("\tMaximum\t")
                    f.write(str(MODEL[score]["maximum"]))
                    f.write("\tMinimum\t")
                    f.write(str(MODEL[score]["minimum"]))
                    f.write("\n")
                f.write("\nF1\tAccuracy\tPrecision\tRecall\n")
                for f1,accuracy,precision,recall in zip(F1["values"],ACCURACY["values"],PRECISION["values"],RECALL["values"]):
                    f.write(str(f1))
                    f.write("\t")
                    f.write(str(accuracy))
                    f.write("\t")
                    f.write(str(precision))
                    f.write("\t")
                    f.write(str(recall))
                    f.write("\n")
                f.close()
        print("Models collected")
        return MODEL
    
    if save:
        if not os.path.isdir("./statistics/"):
            os.mkdir("./statistics/")

    RESULT=[]
    if types:
        RESULT.append(get_types())
    elif status:
        RESULT.append(get_status())
    elif country:
        RESULT.append(get_country())
    elif city:
        RESULT.append(get_city())
    elif list_aff:
        RESULT.append(get_list_aff())
    elif model:
        RESULT.append(get_model())
    else:
        RESULT=[
            get_types(save=save),
            get_status(save=save),
            get_country(save=save),
            get_city(save=save),
            get_model(save=save),
            get_list_aff(save=save)]
    return RESULT

def fast_process(affiliation,country,city,name):
    if country in affiliation and city in affiliation and name in affiliation:
        ROR_ID=db_lit.find_one({"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@"),"name":name})
        if "list_aff" not in ROR_ID:
            db_lit.update_one({"id":ROR_ID["id"]},{"$set":{"list_aff":[affiliation]}})
        elif affiliation not in ROR_ID["list_aff"]:
            db_lit.update_one({"id":ROR_ID["id"]},{"$addToSet":{"list_aff":affiliation}})

def get_aff_requested(request,size=100):

    def sub_process_aff(affiliation,pmid):
        fast_process(affiliation,country,city,name)
        ARRAY=db_lit.find_one({"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@"),"name":name},{"list_aff":1,"id":1})
        os.system('cls' if os.name == 'nt' else 'clear')
        clear_output(wait=True)
        try:
            print("Current country : "+country+" - "+str(country_counter)+"/"+str(country_length))
            print("Current city : "+city+" - "+str(city_counter)+"/"+str(city_length))
            print("Name : "+name+" - "+str(ROR_counter)+"/"+str(ROR_length))
            print("IDs : "+ARRAY["id"])
        except NameError:
            print("Current country : "+country)
            print("Current city : "+city)
            print("Name : "+name)
        print("Request : '"+request+"'")
        try:
            print("Number of affiliations collected : "+str(len(ARRAY["list_aff"])))
        except KeyError:
            print("Number of affiliations collected : 0")
        print("Progress : "+str(pmidCount)+"/"+str(hitCount)+" - "+str(round(pmidCount/hitCount*100,2))+"%")
        print("Current PMID : "+str(pmid))
        if len(TIMES)!=0:
            print("Time estimated : "+str(datetime.timedelta(seconds=int((sum(TIMES)/len(TIMES))*(hitCount-pmidCount)))))
            print("Average PMID time : "+str(round(sum(TIMES)/len(TIMES),2))+"secs")
        print(affiliation)
    
    global pmidCount
    global TIMES
    global hitCount

    cursor="*"
    while True:
        result=searchPOST(request,cursor,resultType="core",size=25)
        hitCount=result["hitCount"]
        if result["nextCursorMark"]==cursor:
            break
        cursor=result["nextCursorMark"]
        ARRAY=db_lit.find_one({"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@"),"name":name},{"list_aff":1})
        if "list_aff" in ARRAY:
            ARRAY=len(ARRAY["list_aff"])
            os.system('cls' if os.name == 'nt' else 'clear')
            print("The request is :"+str(request))
            print("There are "+str(ARRAY)+" unique affiliations in the MongoDB collection.")
            if ARRAY>size:
                break
        else:
            ARRAY=0
        for r in result["resultList"]["result"]:
            if "pmid" not in r:
                result["resultList"]["result"].remove(r)
            elif "authorList" in r and len(r["authorList"]["author"])>200:
                result["resultList"]["result"].remove(r)
        for r in result["resultList"]["result"]:
            ARRAY=db_lit.find_one({"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@"),"name":name},{"list_aff":1})
            if "list_aff" in ARRAY:
                ARRAY=len(ARRAY["list_aff"])
                if ARRAY>size:
                    break
            else:
                ARRAY=0
            start=time.time()
            pmidCount+=1
            if "pmid" in r or ARRAY<size and "pmid" in r:
                if "authorList" in r and len(r["authorList"]["author"])<200:
                    try:
                        for author in r["authorList"]["author"]:
                            try:
                                if "authorAffiliationDetailsList" in author:
                                    for affiliation in author["authorAffiliationDetailsList"]["authorAffiliation"]:
                                        if ";" in affiliation["affiliation"]:
                                            for sub_aff in affiliation["affiliation"].split(";"):
                                                sub_process_aff(sub_aff,r["pmid"])
                                        else:
                                            sub_process_aff(affiliation["affiliation"],r["pmid"])
                                elif "affiliation" in author:
                                    if ";" in author["affiliation"]:
                                        for sub_aff in author["affiliation"].split(";"):
                                            sub_process_aff(sub_aff,r["pmid"])
                                    else:
                                        sub_process_aff(author["affiliation"],r["pmid"])
                            except KeyError:
                                continue
                    except (KeyError, TypeError, IndexError) as error:
                        print("Error : "+str(error))
                        pass
            end=time.time()
            if "pmid" in r or ARRAY<size and "pmid" in r:
                TIMES.append(end-start)

def train_ROR(ROR_ID):
    # problem with organization with a lot of TRUE affiliations and small amount of FALSE affiliations - should be balanced by the model but not sure it is enough

    ORG=db_lit.find_one({"id":ROR_ID})
    true_size=100
    false_size=40
    if "list_aff" in ORG and len(ORG["list_aff"])>=true_size:
        # get False data
        country=ORG["country"]
        city=ORG["city"]
        false_ORG=list(db_lit.find({"country":country,"city":city,"id":{"$ne":ORG["id"]}}))
        nb_aff=0
        for org in false_ORG:
            if "list_aff" in org and ORG["name"] not in org["name"] and org["name"] not in ORG["name"]:
                nb_aff+=len(org['list_aff'])
        if nb_aff>=false_size:
            false_set=[]
            if nb_aff>=100:
                while len(false_set)<len(ORG["list_aff"]):
                    org_pos=random.randint(0,len(false_ORG)-1)
                    if "list_aff" not in false_ORG[org_pos] or len(false_ORG[org_pos]["list_aff"])==0:
                        false_ORG.pop(org_pos)
                    else:
                        aff=false_ORG[org_pos]["list_aff"].pop(random.randint(0,len(false_ORG[org_pos]["list_aff"])-1))
                        if aff not in false_set:
                            false_set.append(aff)
                    if false_ORG==[]:
                        break
            else:
                for org in false_ORG:
                    if "list_aff" in org and ORG["name"] not in org["name"] and org["name"] not in ORG["name"]:
                        false_set=false_set+org["list_aff"]
            data={"Affs":false_set+ORG["list_aff"],"Label":[0]*len(false_set)+[1]*len(ORG["list_aff"])}
            dataset=pandas.DataFrame(data)
            data=None
            vectorizer=TfidfVectorizer(
                ngram_range=(1,len(re.findall(r"[\w]+",ORG["name"]))),
                encoding="utf-8",
                strip_accents="ascii",
                lowercase=True)
            clfLR=LogisticRegressionCV(
                tol=1e-4,
                Cs=[10.0],# See if we need to set more values
                class_weight={
                    0:1-(dataset.Label[dataset.Label==0].shape[0]/dataset.shape[0]),
                    1:1-(dataset.Label[dataset.Label==1].shape[0]/dataset.shape[0])},
                cv=5,
                random_state=42,
                solver='lbfgs',
                max_iter=100,
                multi_class="multinomial")
            X_train,X_test,y_train,y_test=train_test_split(dataset['Affs'],dataset['Label'],random_state=42)
            X_train_tfidf=vectorizer.fit_transform(X_train)
            X_test_tfidf=vectorizer.transform(X_test)
            clfLR.fit(X_train_tfidf,y_train)
            y_pred=clfLR.predict(X_test_tfidf)
            os.system('cls' if os.name == 'nt' else 'clear')
            clear_output(wait=True)
            print(ORG["name"]+" successfully trained!")
            print("Size of the 'True' dataset : "+str(len(ORG["list_aff"])))
            print("Size of the 'False' dataset : "+str(len(false_set)))
            f1=round(metrics.f1_score(y_test,y_pred,average="macro")*100,3)
            print("F1 score : "+str(f1))
            precision=round(metrics.precision_score(y_test,y_pred,average="macro")*100,3)
            print("Precision score : "+str(precision))
            recall=round(metrics.recall_score(y_test,y_pred,average="macro")*100,3)
            print("Recall score : "+str(recall))
            accuracy=round(metrics.accuracy_score(y_test,y_pred)*100,3)
            print("Accuracy score : "+str(accuracy))
            pickled_model=pickle.dumps(clfLR)
            pickled_vectorizer=pickle.dumps(vectorizer)
            if db_lit.find_one({"id":ORG["id"],"model":{"$exists":True}})==None:
                db_lit.update(
                    {"id":ORG["id"]},
                    {"$set":{
                        "model":{
                            "pickled_vectorizer":pickled_vectorizer,
                            "pickled_model":pickled_model,
                            "f1_score":f1,
                            "precision":precision,
                            "recall":recall,
                            "accuracy":accuracy,
                            "training_date":str(datetime.date.today())}}})
            else:
                db_lit.update(
                    {"id":ORG["id"]},
                    {"$set":{
                        "model":{
                            "pickled_vectorizer":pickled_vectorizer,
                            "pickled_model":pickled_model,
                            "f1_score":f1,
                            "precision":precision,
                            "recall":recall,
                            "accuracy":accuracy,
                            "training_date":str(datetime.date.today())}}})
        else:
            print("Not enough '\033[1;31mFalse\033[0;0m' ("+str(nb_aff)+" affiliations/"+str(false_size)+" requested) data to train : \033[1;31m!\033[0;0m\033[;1m\033[1;34m"+ORG["name"]+"\033[0;0m | "+ORG["id"])
            return False
    else:
        print("Not enough '\033[0;32mTrue\033[0;0m' ("+str(len(ORG["list_aff"]))+" affiliations/"+str(true_size)+" requested) data to train : \033[0;32m!\033[0;0m\033[;1m\033[1;34m"+ORG["name"]+"\033[0;0m | "+ORG["id"])
        return False

def predict_ROR(ROR_ID,affiliation):
    ORG=db_lit.find_one({"id":ROR_ID})
    clfLR=pickle.loads(ORG["model"]["pickled_model"])
    vectorizer=pickle.loads(ORG["model"]["pickled_vectorizer"])
    X_test_tfidf=vectorizer.transform([affiliation])
    return clfLR.predict_proba(X_test_tfidf)[0][1]

def build_request(name,city,country):
    if city in name and country in name:
        req=[name]
    elif city in name:
        req=[name,country.replace("_"," ")]
    elif country in name:
        req=[name,city.replace("_"," ").replace("@",".")]
    else:
        req=[name,city.replace("_"," ").replace("@","."),country.replace("_"," ")]
    return req

def train_all(new=False,date="2020-05-29"):
    date=datetime.datetime.strptime(date,"%Y-%m-%d")
    size=39
    if new:
        for ORG in db_lit.find({"list_aff."+str(size):{"$exists":True},"model":{"$exists":False}}).batch_size(10):
            train_ROR(ORG["id"])
    else:
        for ORG in db_lit.find({"list_aff."+str(size):{"$exists":True}}).batch_size(10):
            if "model" in ORG:
                trained_date=datetime.datetime.strptime(ORG["model"]["training_date"],"%Y-%m-%d")
                if date.date() > trained_date.date():
                    train_ROR(ORG["id"])
            else:
                train_ROR(ORG["id"])

if __name__=="__main__":
    if sys.argv[1].startswith("http"):
        ORG=db_lit.find_one({"id":sys.argv[1]})
        country=ORG["country"].replace(" ","_")
        city=ORG["city"].replace(" ","_").replace(".","@")
        name=ORG["name"]
        req=build_request(name,city,country)
        req='AFF:"'+'" AND AFF:"'.join(req)+'"'
        get_aff_requested(req,size=1000)
    else:
        country_req=sys.argv[1]
        country_counter=0
        if not os.path.isdir("./tmp_countries/"):
            os.mkdir("./tmp_countries/")
        dir_path="./tmp_countries/"+country_req
        if not os.path.isdir(dir_path+"/"):
            os.mkdir(dir_path)
            with open(dir_path+"/ROR_scanned.txt","w") as f:
                f.write("")
                f.close()
        country_length=len([country_req])
        for country in [country_req.replace("_"," ")]:
            city_counter=0
            stat=time.time()
            city_length=len(db_lit.distinct("city",{"country":country.replace(" ","_")}))
            en=time.time()
            for city in db_lit.distinct("city",{"country":country.replace(" ","_")}):
                try:
                    with open(dir_path+"/cities.txt","r",encoding="utf-8") as f:
                        CITIES_LIST=f.read()
                        f.close()
                except FileNotFoundError:
                    with open(dir_path+"/cities.txt","w",encoding="utf-8") as f:
                        f.write("")
                        f.close()
                    CITIES_LIST=[]
                city_counter+=1
                city=city.replace("_"," ").replace("@",".")
                if city not in CITIES_LIST:
                    ROR_counter=0
                    ROR_length=len(db_lit.distinct("name",{"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@")}))
                    for name in db_lit.distinct("name",{"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@")}):
                        ROR_counter+=1
                        ARRAY=db_lit.find_one({"country":country.replace(" ","_"),"city":city.replace(" ","_").replace(".","@"),"name":name},{"list_aff":1,"id":1})
                        if "id" in ARRAY:
                            try:
                                with open(dir_path+"/ROR_scanned.txt","r") as f:
                                    RORs_list=f.read()
                                    f.close()
                            except FileNotFoundError:
                                RORs_list=[]
                                with open(dir_path+"/ROR_scanned.txt","w") as f:
                                    f.write("")
                                    f.close()
                            if str(ARRAY["id"]) not in RORs_list:
                                req=build_request(name,city,country)
                                try:
                                    if "list_aff" not in ARRAY or len(ARRAY["list_aff"]) < 100:
                                        pmidCount=0
                                        TIMES=[]
                                        get_aff_requested('AFF:"'+'" AND AFF:"'.join(req)+'"')
                                except KeyError:
                                    pmidCount=0
                                    TIMES=[]
                                    get_aff_requested('AFF:"'+'" AND AFF:"'.join(req)+'"')
                                with open(dir_path+"/ROR_scanned.txt","a") as f:
                                    f.write(ARRAY["id"])
                                    f.write("\n")
                                    f.close()
                    with open(dir_path+"/cities.txt","a",encoding="utf-8") as f:
                        f.write(city)
                        f.write("\t")
        with open(dir_path+"/Done.txt","w") as f:
            f.write("DONE")
            f.close()
