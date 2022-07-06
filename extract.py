#!/usr/bin/env python
#-*- coding: utf-8 -*-
# THOUVENIN Arthur athouvenin@outlook.fr
# 26/02/2020
########################
import datetime # Allows to convert seconds to real time
import json # Allows to load JSON informations
import os # Allows to modify some things on the os
import pickle
import pymongo # Allows to request some Mongo DB
import re # Allows to make regex 
import requests # Allows to make http requests
import time # Allows to set some point in the execution time and then calculate the execution time
import urllib.parse

from sklearn.feature_extraction.text import TfidfVectorizer # Allows transformations of string in number
from sklearn.linear_model import LogisticRegression # Allows to use the Logistic Regression from Scikit-Learn (https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)

##################################################   VARIABLES   ###########################################################
####    VIRTUAL MACHINE    ####
vm="www.ebi.ac.uk"

####    PATHS    ####
dictionaries="./Dictionaries/"

####    MONGO DB    ####
client=pymongo.MongoClient("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
db_lit=client.literature.ROR_testing

####    Dictionaries    ####
with open(dictionaries+"CITIES_light_reverse.json","r",encoding="utf-8") as f:
    reverse_cities_synonyms=json.load(f)
    f.close()
with open(dictionaries+"COUNTRIES_light_reverse.json","r",encoding="utf-8") as f:
    reverse_countries_synonyms=json.load(f)
    f.close()
with open(dictionaries+"REGIONS_light_reverse.json","r",encoding="utf-8") as f:
    reverse_regions_synonyms=json.load(f)
    f.close()

####    Lists    ####
replacements=[ #List of tuples for string preparation (regex pattern, replacement)
    (r'[^\s]+@[^\s]+',' '),
    (r'\\',' '),
    (r'\/',' '),
    (r'-',' '),
    (r'\n',' '),
    (r'\t',' ',),
    (r'^\s*',' '),
    (r'"',"'"),
    (r',\s*$',' '),
    (r'\s.\s',' '),
    (r'^[0-9]+\s|^\s[0-9]+\s',''),
    (r'^\s+',''),
    (r'Electronic address\s*:',''),
    (r'Current address\s*:','')]
TIMES_BY_AFF=[]

headers="PMID\tPMCID\tDOI\tfullName\tfirstName\tlastName\tinitials\tAFF\tBest_name\tROR_ID\tCountry\tCity\tPredict\n"
run=False
##################################################   MAIN   ###########################################################

def is_ORG(request,ORG,city="",country="",proba=True):

    def check_acronyms(request,ORG):
        if len(ORG["acronyms"])>0:
            for acro in ORG["acronyms"]:
                if len(re.findall(rf"[^a-zA-Z0-9]{acro}[^a-zA-Z0-9]|^{acro}[^a-zA-Z0-9]|[^a-zA-Z0-9]{acro}$",request))!=0:
                    return acro
            return False
        else:
            return False

    name = ORG["name"]
    names=[name]+ORG["aliases"]
    tmp_req=" ".join(re.findall(r"[\w]+",request))
    result = {
        "name":ORG["name"],
        "id":ORG["id"],
        "choose":False,
        "score":0.0,
        "method":"",
        "city":ORG["city"],
        "country":ORG["country"],
        "string":request}
    for l in ORG["labels"]:
        names.append(l["label"])
    for n in names:
        n_escape=re.escape(n)
        if len(re.findall(rf"[^a-zA-Z0-9]{n_escape}[^a-zA-Z0-9]|^{n_escape}[^a-zA-Z0-9]|[^a-zA-Z0-9]{n_escape}$",tmp_req,flags=re.IGNORECASE))!=0 and city==ORG["city"].replace("_"," ").replace("@",".") and country==ORG["country"].replace("_"," "):
            result["method"]="Exact match : '"+str(n)+"' "+str(ORG["city"].replace("_"," ").replace("@","."))+" "+str(ORG["country"].replace("_"," "))
            result["choose"]=True
            if proba:
                result["score"]=1.0
            return result
    if "model" in ORG and ORG["model"]["f1_score"]>=75.00:
        result["method"]="Prediction"
        pred_req=request
        for old,new in replacements:
            pred_req=re.sub(old,new,pred_req)
        Vectori=pickle.loads(ORG["model"]["pickled_vectorizer"])
        Model=pickle.loads(ORG["model"]["pickled_model"])
        X_test_tfidf=Vectori.transform([request])
        y_pred=Model.predict_proba(X_test_tfidf)
        ## Default value score & site
        first_name=re.findall(r'[\w]+',name)[0]
        if proba:
            result["score"]=round(y_pred[0][1],2)
        if y_pred[0][1]>0.9:
            result["method"]="Prediction on complete sentence"
            result["choose"]=False
            return result
        elif y_pred[0][1]>0.6 or first_name in request:
            if ";" in request:
                for aff in request.split(";"):
                    is_org=is_ORG(aff,ORG,proba=proba)
                    if is_org["score"]>0.9:
                        is_org["method"]="Prediction on substring ';' / "+is_org["method"]
                        is_org["substring"]=aff
                        is_org["string"]=request
                        return is_org
            elif first_name in request:
                sent=re.findall(r'[\w]+',request)
                indices=[i for i,x in enumerate(sent) if x==first_name]
                for indice in indices:
                    limit=6
                    if indice+limit>len(sent):
                        limit=-1
                    else:
                        limit+=indice
                    sub_str=" ".join(sent[indice:limit])
                    X_test_tfidf=Vectori.transform([sub_str])
                    y_pred=Model.predict_proba(X_test_tfidf)
                    if y_pred[0][1]>0.9:
                        result["method"]="Prediction on substring"
                        result["substring"]=sub_str
                        result["string"]=request
                        return result
            else:
                acronyms=check_acronyms(request,ORG)
                if acronyms:
                    result["choose"]=True
                    result["method"]="Acronyms : '"+str(acronyms)+"'"
                    result["score"]=1.0
                    return result
    acronyms=check_acronyms(request,ORG)
    if acronyms:
        result["choose"]=True
        result["method"]="Acronyms : '"+str(acronyms)+"'"
        result["score"]=1.0
        return result
    return result

def build_CITIES_dict(filename="CITIES",light=False):

    if not os.path.exists(dictionaries+"weird_cities.txt"):
        with open(file=dictionaries+"weird_cities.txt",mode='w',encoding="utf-8") as f:
            f.write("")
            f.close()
    with open(file=dictionaries+"weird_cities.txt",mode="r",encoding="utf-8") as f:
        weird_cities=f.read()
        f.close()
    
    def reverse_dict(dictionary={}):
        NEW_DICT={}
        for item_co in dictionary:
            if item_co not in NEW_DICT:
                NEW_DICT[item_co]={}
            for item_ci in dictionary[item_co]:
                for synonym in dictionary[item_co][item_ci]:
                    if synonym not in NEW_DICT[item_co]:
                        NEW_DICT[item_co][synonym]=[item_ci]
                    else:
                        NEW_DICT[item_co][synonym].append(item_ci)
        return NEW_DICT

    def cities_check(country,DICT,off_langs):
        for city in db_lit.distinct("city",{"country":country}):
            if city not in DICT[country] and city not in weird_cities:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Country : "+country.replace("_"," "))
                print("City : "+city.replace("_"," ").replace("@","."))
                print("*"+city+"*")
                print("http://api.geonames.org/search?q="+country.replace("_"," ")+" , "+city.replace("_"," ").replace("@",".")+"&maxRows=1&featureClass=P&username=alphazero")
                if country=="Aland_Islands":
                    req1=requests.get("http://api.geonames.org/search?q=AX , "+city.replace("_"," ").replace("@",".")+"&maxRows=1&featureClass=P&username=alphazero")
                else:
                    req1=requests.get("http://api.geonames.org/search?q="+country.replace("_"," ")+" , "+city.replace("_"," ").replace("@",".")+"&maxRows=1&featureClass=P&username=alphazero")
                geonameId=re.search(r"<geonameId>(.*)</geonameId>",req1.text).group(1)
                req2=requests.get("http://api.geonames.org/get?geonameId="+geonameId+"&username=alphazero")
                if "city" not in re.search(r"<fclName>(.*)</fclName>",req2.text).group(1):
                    print(req2.text)
                    input()
                else:
                    if light:
                        try:
                            langs=off_langs[re.search(r"<countryCode>([a-zA-Z]+)</countryCode>",req2.text).group(1)]
                            tmp=[]
                            for alternateName in re.findall(r"<alternateName\s[a-zA-Z\s\"=]*lang=\"([a-z]+)\">([^<]+)</alternateName>",req2.text):
                                lang=alternateName[0]
                                a_name=alternateName[1]
                                if lang in langs and a_name not in tmp:
                                    tmp.append(a_name)
                            DICT[country][city]=tmp
                        except AttributeError:
                            DICT[country][city]=[]
                    else:
                        try:
                            DICT[country][city]=re.sub(r"[\n\t]+","",re.search(r"<alternateNames>(.*)</alternateNames>",req2.text).group(1)).split(",")
                        except AttributeError:
                            DICT[country][city]=[]
                with open(dictionaries+filename+".json","w",encoding="utf-8") as f:
                    json.dump(DICT,f,indent=4)
                    f.close()

    if light:
        filename=filename+"_light"
        off_langs={}
        with open(file=dictionaries+"country_lang.csv",mode="r",encoding="utf-8") as f:
            for line in f.readlines():
                if line=="\n":
                    continue
                line=line.split("\t")
                off_langs[line[0]]=["en"]
                for l in line[9].split(","):
                    if "-" in l:
                        off_langs[line[0]].append(l.split("-")[0])
                    else:
                        off_langs[line[0]].append(l)
            f.close()
    if not os.path.exists(dictionaries+filename+".json"):
        with open(dictionaries+filename+".json", 'w') as f:
            f.write("{}")
            f.close()
    for country in db_lit.distinct("country"):
        with open(dictionaries+filename+".json","r",encoding="utf-8") as f:
            DICT=json.load(f)
            f.close()
        if country not in DICT:
            DICT[country]={}
            with open(dictionaries+filename+".json","w",encoding="utf-8") as f:
                json.dump(DICT,f,indent=4)
                f.close()
        if len(DICT[country])!=len(db_lit.distinct("city",{"country":country})):
            cities_check(country,DICT,off_langs)
    with open(dictionaries+filename+".json","w",encoding="utf-8") as f:
        json.dump(DICT,f,indent=4)
        f.close()
    with open(dictionaries+filename+"_reverse.json","w",encoding="utf-8") as f:
        json.dump(reverse_dict(DICT),f,indent=4)
        f.close()

def build_COUNTRIES_dict(filename="COUNTRIES",light=False):

    def reverse_dict(dictionary={}):
        NEW_DICT={}
        for item in dictionary:
            for synonym in dictionary[item]:
                if synonym not in NEW_DICT:
                    NEW_DICT[synonym]=[item]
                else:
                    NEW_DICT[synonym].append(item)
        return NEW_DICT

    DICT={}
    if light:
        filename=filename+"_light"
        off_langs={}
        with open(file=dictionaries+"/country_lang.csv",mode="r",encoding="utf-8") as f:
            for line in f.readlines():
                if line=="\n":
                    continue
                line=line.split("\t")
                off_langs[line[0]]=["en"]
                for l in line[9].split(","):
                    if "-" in l:
                        off_langs[line[0]].append(l.split("-")[0])
                    else:
                        off_langs[line[0]].append(l)
            f.close()
    if not os.path.exists(dictionaries+filename+".json"):
        with open(dictionaries+filename+".json", 'w') as f:
            f.write("{}")
            f.close()
    for country in db_lit.distinct("country"):
        with open(dictionaries+filename+".json","r",encoding="utf-8") as f:
            DICT=json.load(f)
            f.close()
        if country not in DICT:
            req1=requests.get("http://api.geonames.org/search?q="+country.replace("_"," ")+"&maxRows=1&featureClass=A&username=alphazero")
            geonameId=re.search(r"<geonameId>(.*)</geonameId>",req1.text).group(1)
            req2=requests.get("http://api.geonames.org/get?geonameId="+geonameId+"&username=alphazero")
            if "country" not in re.search(r"<fclName>(.*)</fclName>",req2.text).group(1):
                print(req2.text)
                input("Please be careful the match is not a country!!!")
            else:
                if light:
                    try:
                        langs=off_langs[re.search(r"<countryCode>([a-zA-Z]+)</countryCode>",req2.text).group(1)]
                        tmp=[]
                        for alternateName in re.findall(r"<alternateName\s[a-zA-Z\s\"=]*lang=\"([a-z]+)\">([^<]+)</alternateName>",req2.text):
                            lang=alternateName[0]
                            a_name=alternateName[1]
                            if lang in langs and a_name not in tmp:
                                tmp.append(a_name)
                        DICT[country]=tmp
                    except AttributeError:
                        DICT[country]=[]
                else:
                    try:
                        DICT[country]=re.sub(r"[\n\t]+","",re.search(r"<alternateNames>(.*)</alternateNames>",req2.text).group(1)).split(",")
                    except AttributeError:
                        DICT[country]=[]
        with open(dictionaries+filename+".json","w",encoding="utf-8") as f:
            json.dump(DICT,f,indent=4)
            f.close()
        with open(dictionaries+filename+"_reverse.json","w",encoding="utf-8") as f:
            json.dump(reverse_dict(DICT),f,indent=4)
            f.close()

def build_regions_states_dict(filename="REGIONS",light=False):

    off_langs={}

    def reverse_dict(dictionary={}):
        NEW_DICT={}
        for item in dictionary:
            for synonym in dictionary[item]:
                if synonym not in NEW_DICT:
                    NEW_DICT[synonym]=[item]
                else:
                    NEW_DICT[synonym].append(item)
        return NEW_DICT

    def get_alternate_names(geonameId,light,off_langs):
        NAMES=[]
        req=requests.get("http://api.geonames.org/get?geonameId="+geonameId+"&username=alphazero")
        if light:
            try:
                langs=off_langs[re.search(r"<countryCode>([a-zA-Z]+)</countryCode>",req.text).group(1)]
                for alternateName in re.findall(r"<alternateName\s[a-zA-Z\s\"=]*lang=\"([a-z]+)\">([^<]+)</alternateName>",req.text):
                    lang=alternateName[0]
                    a_name=alternateName[1]
                    if lang in langs and a_name not in NAMES:
                        NAMES.append(a_name)
            except AttributeError:
                pass
        else:
            try:
                NAMES=re.sub(r"[\n\t]+","",re.search(r"<alternateNames>(.*)</alternateNames>",req.text).group(1)).split(",")
            except AttributeError:
                pass
        return NAMES

    particular_countries=[
        "United_Kingdom"]
    DICT={}
    if light:
        filename=filename+"_light"
        off_langs={}
        with open(file=dictionaries+"country_lang.csv",mode="r",encoding="utf-8") as f:
            for line in f.readlines():
                if line=="\n":
                    continue
                line=line.split("\t")
                off_langs[line[0]]=[]
                for l in line[9].split(","):
                    if "-" in l:
                        off_langs[line[0]].append(l.split("-")[0])
                    else:
                        off_langs[line[0]].append(l)
            f.close()
    if not os.path.exists(dictionaries+filename+".json"):
        with open(dictionaries+filename+".json", 'w') as f:
            f.write("{}")
            f.close()
    for country in db_lit.distinct("country"):
        with open(dictionaries+filename+".json","r",encoding="utf-8") as f:
            DICT=json.load(f)
            f.close()
        TMP=[]
        if country not in DICT:
            req1=requests.get("http://api.geonames.org/search?q="+country.replace("_"," ")+"&maxRows=1&featureClass=A&username=alphazero")
            req2=requests.get("http://api.geonames.org/children?geonameId="+str(re.search(r"<geonameId>(.*)</geonameId>",req1.text).group(1))+"&username=alphazero&hierarchy=geography")
            for ident in re.findall(r"<geonameId>(.*)</geonameId>",req2.text):
                if country in particular_countries:
                    req3=requests.get("http://api.geonames.org/children?geonameId="+str(ident)+"&username=alphazero&hierarchy=geography")
                    for ide in re.findall(r"<geonameId>(.*)</geonameId>",req3.text):
                        TMP=TMP+get_alternate_names(ide,light,off_langs)
                else:
                    TMP=TMP+get_alternate_names(ident,light,off_langs)
            DICT[country]=TMP
            with open(dictionaries+filename+".json","w",encoding="utf-8") as f:
                json.dump(DICT,f,indent=4)
                f.close()
    with open(dictionaries+filename+"_reverse.json","w",encoding="utf-8") as f:
        json.dump(reverse_dict(DICT),f,indent=4)
        f.close()

def get_ROR(affiliation,treshold=0.7):

    RESULT=[]
    country_found=[]
    ORGS=[]
    
    def process_city(affiliation,country="",treshold=treshold):

        def process_ROR(affiliation,country="",city="",treshold=treshold):

            def get_ROR_API(affiliation,country="",city="",treshold=treshold):
                ROR_API_score=0.6
                ROR_RESULT=[]
                ROR_req=requests.get("https://api.ror.org/organizations?affiliation="+urllib.parse.quote(affiliation))
                ROR_req=ROR_req.json()
                if ROR_req["number_of_results"]>0:
                    RESULT_TMP=[]
                    for result in ROR_req["items"]:
                        pot_org=db_lit.find_one({"id":result["organization"]["id"]},{"id":1,"name":1,"model":1,"acronyms":1,"labels":1,"aliases":1,"city":1,"country":1})
                        if pot_org != None:
                            ORGS.append(result["organization"]["id"])
                            res=is_ORG(affiliation,pot_org,city=city,country=country,proba=True)
                            res["ROR_API"]=True
                            res["ROR_API_score"]=result["score"]
                            if result["score"]>=ROR_API_score:
                                RESULT_TMP.append(res)
                            if country !="" and country==pot_org["country"] and result["score"]>=ROR_API_score:
                                ROR_RESULT.append(res)
                            elif result["score"]>=0.9:
                                ROR_RESULT.append(res)
                    if len(ROR_RESULT)==0:
                        ROR_RESULT=RESULT_TMP
                for result in ROR_RESULT:
                    result["avg"]=round((result["score"]+result["ROR_API_score"])/2,2)
                return ROR_RESULT
            
            RESULT_ROR=[]
            if country != "":
                if city != "":
                    for org in db_lit.find({"country":country,"city":city},{"id":1,"name":1,"model":1,"acronyms":1,"labels":1,"aliases":1,"city":1,"country":1}):
                        if org["id"] not in ORGS:
                            ORGS.append(org["id"])
                            res=is_ORG(affiliation,org,country=country,city=city,proba=True)
                            if res["score"]>=treshold:
                                RESULT_ROR.append(res)
            else:
                if city != "":
                    for org in db_lit.find({"city":city},{"id":1,"name":1,"model":1,"acronyms":1,"labels":1,"aliases":1,"city":1,"country":1}):
                        if org["id"] not in ORGS:
                            ORGS.append(org["id"])
                            res=is_ORG(affiliation,org,country=country,city=city,proba=True)
                            if res["score"]>=treshold:
                                RESULT_ROR.append(res)
            if len(RESULT_ROR)==0:
                RESULT_ROR=get_ROR_API(affiliation,country=country,city=city,treshold=treshold)
            return RESULT_ROR
        
        """
        def check_cities_synonyms(synonyms_dict,affiliation,country):
            tmp=[]
            for c in cities_synonyms[country]:
                found=False
                for synonym in cities_synonyms[country][c]:
                    sy=re.escape(synonym)
                    if len(re.findall(rf"[^a-zA-Z0-9]{sy}[^a-zA-Z0-9]|^{sy}[^a-zA-Z0-9]|[^a-zA-Z0-9]{sy}$",affiliation,flags=re.IGNORECASE))!=0:
                        affiliation=re.sub(rf"([^a-zA-Z0-9]?)({sy})([^a-zA-Z0-9]?)",r"\1"+c.replace("_"," ").replace("@",".")+r"\3",affiliation,flags=re.IGNORECASE) # MAYBE NEED TO VERIFY
                        found=True
                        break
                if found and c not in tmp:
                    tmp.append(c)
            return tmp
        """

        CITY=[]
        RESULT=[]
        if country != "":
            cities=[c.replace("_"," ").replace("@",".") for c in db_lit.distinct("city",{"country":country.replace(" ","_")})]
        else:
            cities=[c.replace("_"," ").replace("@",".") for c in db_lit.distinct("city")]
        CITY=CITY+[i for i in cities if len(re.findall(rf"[^a-zA-Z0-9]{i}[^a-zA-Z0-9]|^{i}[^a-zA-Z0-9]|[^a-zA-Z0-9]{i}$",affiliation,flags=re.IGNORECASE))!=0]
        if len(CITY)==0:
            if country != "":
                for p in reverse_cities_synonyms[country]:
                    p_escape=re.escape(p)
                    if len(re.findall(rf"[^a-zA-Z0-9]{p_escape}[^a-zA-Z0-9]|^{p_escape}[^a-zA-Z0-9]|[^a-zA-Z0-9]{p_escape}$",affiliation,flags=re.IGNORECASE))!=0 and reverse_cities_synonyms[country][p] not in CITY:
                        CITY.append(reverse_cities_synonyms[country][p])
            else: # Maybe use spacy??? NER???
                for Co in db_lit.distinct("country"):
                    for p in reverse_cities_synonyms[Co]:
                        p_escape=re.escape(p)
                        if len(re.findall(rf"[^a-zA-Z0-9]{p_escape}[^a-zA-Z0-9]|^{p_escape}[^a-zA-Z0-9]|[^a-zA-Z0-9]{p_escape}$",affiliation,flags=re.IGNORECASE))!=0 and reverse_cities_synonyms[Co][p] not in CITY:
                            CITY.append(reverse_cities_synonyms[Co][p])
            CITY=list(dict.fromkeys([item for sublist in CITY for item in sublist]))
        else:
            CITY=list(dict.fromkeys(CITY))
        if len(CITY)==0:
            RESULT=process_ROR(affiliation,country=country,city="")
        else:
            if country=="":
                for ci in CITY:
                    for C in db_lit.distinct("country",{"city":ci}):
                        for o in process_ROR(affiliation,country=C,city=ci):
                            if not any(b["id"]==o["id"] for b in RESULT):
                                RESULT.append(o)
            else:
                for c in CITY:
                    for o in process_ROR(affiliation,country=country,city=c):
                        if not any(b["id"]==o["id"] for b in RESULT):
                            RESULT.append(o)
        N_RESULT=[]
        for R in RESULT:
            if "ROR_API" not in R:
                N_RESULT.append(R)
        if len(N_RESULT)>0:
            RESULT=N_RESULT
        return RESULT

    """def check_countries_synonyms(synonyms_dict,affiliation):
        tmp=[]
        for C in synonyms_dict:
            found=False
            for synonym in synonyms_dict[C]:
                sy=re.escape(synonym)
                if len(re.findall(rf"[^a-zA-Z0-9]{sy}[^a-zA-Z0-9]",affiliation,flags=re.IGNORECASE))!=0:
                    affiliation=re.sub(rf"([^a-zA-Z0-9])({sy})([^a-zA-Z0-9])",r"\1"+C.replace("_"," ").replace("@",".")+r"\3",affiliation,flags=re.IGNORECASE)
                    found=True
                    break
            if found and C not in tmp:
                tmp.append(C)
        return tmp"""

    if len(re.findall(r'[\w]+',affiliation))<5:
        return []
    for co in db_lit.distinct("country"):
        if co.replace("_"," ") in affiliation and co not in country_found:
            country_found.append(co)
    if len(country_found)==0:
        for p in reverse_countries_synonyms:
            p_escape=re.escape(p)
            if len(re.findall(rf"[^a-zA-Z0-9]{p_escape}[^a-zA-Z0-9]|^{p_escape}[^a-zA-Z0-9]|[^a-zA-Z0-9]{p_escape}$",affiliation,flags=re.IGNORECASE))!=0 and reverse_countries_synonyms[p] not in country_found:
                country_found.append(reverse_countries_synonyms[p])
        country_found=list(dict.fromkeys([item for sublist in country_found for item in sublist]))
        if len(country_found)==0:
            for p in reverse_regions_synonyms:
                p_escape=re.escape(p)
                if len(re.findall(rf"[^a-zA-Z0-9]{p_escape}[^a-zA-Z0-9]|^{p_escape}[^a-zA-Z0-9]|[^a-zA-Z0-9]{p_escape}$",affiliation,flags=re.IGNORECASE))!=0 and reverse_regions_synonyms[p] not in country_found:
                    country_found.append(reverse_regions_synonyms[p])
            country_found=list(dict.fromkeys([item for sublist in country_found for item in sublist]))
    if len(country_found)!=0:
        for co in country_found:
            for m in process_city(affiliation,country=co):
                if not any(b["id"]==m["id"] for b in RESULT):
                    RESULT.append(m)
    else:
        RESULT=process_city(affiliation,country="")
    nb_RORAPI=0
    for r in RESULT:
        if "ROR_API" in r:
            nb_RORAPI+=1
    if len(RESULT)!=nb_RORAPI:
        RESULT=sorted(RESULT,key=lambda l: l["score"])
        score="score"
    else:
        RESULT=sorted(RESULT,key=lambda l: l["avg"])
        score="avg"
    nb1=0
    for res in RESULT:
        if res[score]==1.0:
            nb1+=1
    if nb1>1:
        ACRO=[]
        PRED=[]
        EXAC=[]
        SC1=[]
        for res in RESULT:
            if res[score]==1.0:
                SC1.append(res)
        for res in SC1:
            if "Acronyms" in res["method"]:
                ACRO.append(res)
            elif "Prediction" in res["method"]:
                PRED.append(res)
            elif "Exact match" in res["method"]:
                EXAC.append(res)
            RESULT.remove(res)
        ACRO=sorted(ACRO, key=lambda l: len(l["method"].split("'")[1]),reverse=False)
        EXAC=sorted(EXAC, key=lambda l: len(l["method"].split("'")[1]),reverse=False)
        RESULT=RESULT+ACRO+PRED+EXAC
    return RESULT

def save_aff(string,pmid,fullName="",firstName="",lastName="",initials="",no_duplicates=False,filename="RESULT.csv",pmcid="",doi=""):
    found=False
    with open("./Results/"+filename,"r",encoding="utf-8") as f:
        table=f.read()
        if string in table:
            found=re.findall(rf"{re.escape(string)}\t[^\n]+",table)
            if len(found)<1:
                found=False
            else:
                found=found[0]
            table=""
            f.close()
    if no_duplicates and found:
        return
    if found:
        resname=found.split("\t")[1]
        resrorid=found.split("\t")[2]
        rescountry=found.split("\t")[3]
        rescity=found.split("\t")[4]
        res=found.split("\t")[5]
    else:
        res=get_ROR(str(string))
        if len(res)>0:
            resname=res[-1]["name"]
            resrorid=res[-1]["id"]
            rescountry=res[-1]["country"]
            rescity=res[-1]["city"]
        else:
            resname,resrorid,rescountry,rescity=" "," "," "," "
    with open("./Results/"+filename,"a",encoding="utf-8") as f:
        f.write(pmid)
        f.write("\t")
        f.write(pmcid)
        f.write("\t")
        f.write(doi)
        f.write("\t")
        f.write(fullName)
        f.write("\t")
        f.write(firstName)
        f.write("\t")
        f.write(lastName)
        f.write("\t")
        f.write(initials)
        f.write("\t")
        f.write(string)
        f.write("\t")
        f.write(resname)
        f.write("\t")
        f.write(resrorid)
        f.write("\t")
        f.write(rescountry)
        f.write("\t")
        f.write(rescity)
        f.write("\t")
        f.write(str(res))
        f.write("\n")
        f.close()

def find_my_org(rorid=""):
    return db_lit.find_one({"id":rorid})

def searchPOST(request,cursor="*",size=1000,resultType="idlist"):
    postm={
        "query":str(request),
        "resultType":resultType,
        "pageSize":size,
        "format":"json",
        "cursorMark":cursor}
    url="https://"+vm+"/europepmc/webservices/rest/searchPOST"
    req=requests.post(url,data=postm)
    query=json.loads(req.text)
    if "hitCount" in query:
        hitCount=query["hitCount"]
        print("HitCount : "+str(hitCount))
    else:
        print(req.text)
    return query

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    LST=[]
    for i in range(0, len(lst), n):
        LST.append(lst[i:i + n])
    return LST

def process_result(result,resultfile,no_duplicates=False,last_pmid=headers):

    def sub_process(aff,r,fullName,firstName,lastName,initials,resultfile,no_duplicates=False):
        global TIMES_BY_AFF
        st=time.time()
        if "doi" in r:
            doi=r["doi"]
        else:
            doi=""
        if "pmcid" in r:
            pmcid=r["pmcid"]
        else:
            pmcid=""
        save_aff(aff,r["pmid"],fullName=fullName,firstName=firstName,lastName=lastName,initials=initials,no_duplicates=no_duplicates,filename=resultfile,pmcid=pmcid,doi=doi)
        en=time.time()
        TIMES_BY_AFF.append(en-st)
        os.system('cls' if os.name == 'nt' else 'clear')
        print("PMID : "+r["pmid"])
        print(aff)
        print("AVG : "+str(round(sum(TIMES_BY_AFF)/len(TIMES_BY_AFF),2))+" secs")
        print("Current : "+str(round(en-st,2))+" secs")
        print("MAX : "+str(round(max(TIMES_BY_AFF),2))+" secs")
        print("MIN : "+str(round(min(TIMES_BY_AFF),2))+" secs")

    global TIMES_BY_AFF
    global run
    for r in result["resultList"]["result"]:
        if "pmid" in r:
            if last_pmid==headers or r["pmid"]==last_pmid or run:
                run=True
                if "authorList" not in r:
                    with open("./TMP/noAuthorListPmids.txt","a",encoding="utf-8") as f:
                        f.write(r["pmid"])
                        f.write("\n")
                        f.close()
                else:
                    for author in r["authorList"]["author"]:
                        if "fullName" in author:
                            fullName=author["fullName"]
                        else:
                            fullName=""
                        if "firstName" in author:
                            firstName=author["firstName"]
                        else:
                            firstName=""
                        if "lastName" in author:
                            lastName=author["lastName"]
                        else:
                            lastName=""
                        if "initials" in author:
                            initials=author["initials"]
                        else:
                            initials=""
                        if "authorAffiliationDetailsList" in author:
                            for affiliation in author["authorAffiliationDetailsList"]["authorAffiliation"]:
                                if ";" in affiliation["affiliation"]:
                                    for sub_aff in affiliation["affiliation"].split(";"):
                                        sub_process(sub_aff,r,fullName,firstName,lastName,initials,resultfile)
                                else:
                                    sub_process(affiliation["affiliation"],r,fullName,firstName,lastName,initials,resultfile)
                        elif "affiliation" in author:
                            affiliation=author["affiliation"]
                            if ";" in affiliation:
                                for sub_aff in affiliation.split(";"):
                                    sub_process(sub_aff,r,fullName,firstName,lastName,initials,resultfile)
                            else:
                                sub_process(affiliation,r,fullName,firstName,lastName,initials,resultfile)

def extract_PMIDs(file):
    if ".txt" in file or ".csv" in file:
        PMIDS=[]
        with open(file,"r") as f:
            tmp=f.read()
            if "PMID:" in tmp:
                PMIDS=re.findall(r"PMID:([0-9]+),",tmp)
            else:
                PMIDS=re.findall(r"[0-9]+",tmp)
            f.close()
            tmp=None
    else:
        PMIDS=re.findall(r"[0-9]+",file)
    return PMIDS

def last_PMID_processed(resultfile):
    if not os.path.exists("./Results/"+resultfile):
        with open("./Results/"+resultfile,"w+",encoding="utf-8") as f:
            f.write(headers)
            f.close()
        last_pmid=headers
    else:
        with open("./Results/"+resultfile,"r", encoding="utf-8") as f:
            try:
                last_pmid=f.readlines()[-1]
            except IndexError:
                last_pmid=""
            if last_pmid!="":
                last_pmid=last_pmid.split("\t")[0]
                if last_pmid=="PMID":
                    last_pmid=headers
                else:
                    print("Last PMID processed : "+last_pmid)
            f.close()
        with open("./Results/"+resultfile,"r",encoding="utf-8") as oldfile, open("./Results/"+'TMP.csv','w',encoding="utf-8") as newfile:
            for line in oldfile:
                if not last_pmid+"\t" in line:
                    newfile.write(line)
        os.remove("./Results/"+resultfile)
        os.rename("./Results/TMP.csv","./Results/"+resultfile)
    return last_pmid

def tag_PMIDs(PMIDs_file="test.csv",resultfile="test.tsv",no_duplicates=False):
    PMIDS=extract_PMIDs(PMIDs_file)
    print("List collected, "+str(len(PMIDS))+" PMIDs ready to process.")
    if len(PMIDS)==0:
        return
    last_pmid=last_PMID_processed(resultfile)
    cursor="*"
    size=500
    if len(PMIDS)<size:
        result=searchPOST('ext_id:'+' OR ext_id:'.join(PMIDS),cursor,resultType="core")
        process_result(result,resultfile,no_duplicates=no_duplicates,last_pmid=last_pmid)
    else:
        for batch in chunks(PMIDS,size):
            print("Batch length : "+str(len(batch)))
            result=searchPOST('ext_id:'+' OR ext_id:'.join(batch),cursor,resultType="core")
            process_result(result,resultfile,no_duplicates=no_duplicates,last_pmid=last_pmid)

class Pretty:

    def __init__(self):
        super().__init__()
    
    def get_ROR(self):
        affiliation=input("\033[1mEnter your affiliation and press 'Enter' : \x1b[0m\n")
        st=time.time()
        r=get_ROR(affiliation,treshold=0.7)[-1]
        print("Name : \033[34m\033[1m"+r["name"]+"\x1b[0m")
        print("ID : "+r["id"])
        print("City : "+r["city"])
        print("City : "+r["country"])
        en=time.time()
        print("\nAssignation last : "+str(round(en-st,0))+" secs.")
    
    def PMID_to_ROR(self):

        def process_aff(affiliation):
            st=time.time()
            org=get_ROR(affiliation)
            if len(org)>0:
                org=org[-1]
            else:
                org=None
            en=time.time()
            print("\nAFF : "+affiliation)
            if org != None:
                print("Name : \033[34m\033[1m"+org["name"]+"\x1b[0m")
                print("ID : "+org["id"])
                print("City : "+org["city"])
                print("Country : "+org["country"])
            else:
                print("###  NOT FOUND  ###")
            print("Assignation last : "+str(round(en-st,0))+" secs.")
            return org

        ORGANIZATIONS=[]
        PMID=input("\033[1mEnter a PMCID in the following format 'PMID:00000000' and press 'Enter' : \x1b[0m\n")
        PMID=PMID.split(":")[1]
        search=searchPOST("ext_id:"+PMID,cursor="*",resultType="core",size="1")
        for r in search["resultList"]["result"]:
            if "pmid" in r:
                for author in r["authorList"]["author"]:
                    if "authorAffiliationDetailsList" in author:
                        for affiliation in author["authorAffiliationDetailsList"]["authorAffiliation"]:
                            if ";" in affiliation["affiliation"]:
                                for sub_aff in affiliation["affiliation"].split(";"):
                                    x=process_aff(sub_aff)
                                    if x != None:
                                        ORGANIZATIONS.append(process_aff(sub_aff))
                            else:
                                x=process_aff(affiliation["affiliation"])
                                if x != None:
                                    ORGANIZATIONS.append(process_aff(affiliation["affiliation"]))
                    elif "affiliation" in author:
                        if ";" in author["affiliation"]:
                            for sub_aff in author["affiliation"].split(";"):
                                x=process_aff(sub_aff)
                                if x != None:
                                    ORGANIZATIONS.append(process_aff(sub_aff))
                        else:
                            x=process_aff(affiliation)
                            if x != None:
                                ORGANIZATIONS.append(process_aff(affiliation))
        COUNTRY_DICT={}
        for r in ORGANIZATIONS:
            if r["country"] not in COUNTRY_DICT:
                COUNTRY_DICT[r["country"].replace("_"," ")]=1
            else:
                COUNTRY_DICT[r["country"].replace("_"," ")]=COUNTRY_DICT[r["country"]]+1
        from mapping import map_display
        map_display("Affiliated country in "+PMID,COUNTRY_DICT)

    def ROR_API_call(self,best=True):
        AFF=input("Enter your affiliation : \n")
        ROR_req=requests.get("https://api.ror.org/organizations?affiliation="+AFF)
        ROR_req=ROR_req.json()
        if best:
            return ROR_req["items"][0]
        else:
            return ROR_req


if __name__=="__main__":
    tag_PMIDs(PMIDs_file="europepmc_id.txt",resultfile="test.tsv")
