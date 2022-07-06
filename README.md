<p align="center"><img width=30% src="https://www.ebi.ac.uk/eva/img/dbSNP/EMBL_EBI-logo.png"></p>
<p align="center"><img width=20% src="https://www.infodocket.com/wp-content/uploads/2020/06/2020-06-02_09-17-36.png"></p>



<h1 align="center"> ROR-prototype-EMBL </h1> <br>
<p align="center">
  ROR prototype developed during the FREYA project
</p>

![Python](https://img.shields.io/badge/Python-v3.5%2B-blue)
![Confluence](https://img.shields.io/badge/Confluence-FREYA%2FEMBL%20project-green)

## Clone
```bash
git clone https://github.com/0AlphaZero0/ROR-prototype-EMBL.git
```

## Table of Contents

- [Introduction](#introduction)
- [Running](#running)
- [Details](#details)
  - [extract](#extract)
  - [manage](#manage)
  - [mapping](#mapping)


## Introduction
This project take place in the FREYA project. The goal was to disambiguate institutions names within affiliations thanks to the [ROR database](https://ror.org/). A tool has already been developped, by DataCite, the [ROR API](https://github.com/ror-community/ror-api). However, it seems this API is does not provide good performances for the *EMBL* organization. Indeed, for all EMBL sites the ROR API revealed a 70% reliability score (mostly due to the mismatching between [EMBL Heidelberg](https://ror.org/03mstc592) and [EMBL Hamburg](https://ror.org/050589e39)).
All this project can be found on this **[`Confluence`](https://www.ebi.ac.uk/seqdb/confluence/x/cyDpBg)** page.

This prototype aims to match with a good precision, based on machine learning models, at least one ROR ID to one affiliation. To be able to increase the performances of the ROR API the ROR database has been clone to a collection in Europe PMC MongoDB. Thus it is necessary to have an access to the Mongo collection to run this prototype and thus a connexion to the EMBL-EBI VPN. Each institution in the database follow the same organization :

<details><summary>Institution preview</summary>
<p>
  
  ```
{
 "_id" : ObjectId("5e4fa3eb57704cb3ebb8d226"),
 "types" : ["Education"],
 "name" : "Australian National University",
 "labels" : [],
 "links" : ["http://www.anu.edu.au/"],
 "acronyms" : ["ANU"],
 "wikipedia_url" : "http://en.wikipedia.org/wiki/Australian_National_University",
 "aliases" : [],
 "id" : "https://ror.org/019wvm592",
 "external_ids" : {
     "FundRef" : {
         "all" : ["501100000995","100009020","501100001151"],
         "preferred" : "501100000995"},
     "ISNI" : {
         "all" : ["0000 0001 2180 7477"],
         "preferred" : null},
     "GRID" : {
         "all" : "grid.1001.0",
         "preferred" : "grid.1001.0"},
     "OrgRef" : {
         "all" : ["285106"],
         "preferred" : null},
     "Wikidata" : {
         "all" : ["Q127990"],
         "preferred" : null}
     },
 "status" : "active",
 "country" : "Australia",
 "city" : "Canberra",
 "list_aff" : [
     "John Curtin School of Medical Research, The Australian National University, Canberra, Australia.",
     "Eccles Institute of Neuroscience, John Curtin School of Medical Research, the Australian National University , Canberra , Australia.",
     " Centre for Research on Ageing, Health and Wellbeing, Australian National University, Canberra, Australia. Electronic address: rebecca.mcketin@curtin.edu.au.",
     "Centre for Research on Ageing, Health and Wellbeing, Australian National University, Canberra, Australia. Electronic address: u5513662@anu.edu.au.",
      ...
     "Academic Unit of General Practice, Australian National University Medical School, Canberra, Australian Capital Territory, Australia.",
     "Social Foundations of Medicine, Australian National University Medical School, Canberra, Australian Capital Territory, Australia.",
     "Research School of Engineering, Australian National University, Canberra, ACT, 0200, Australia. guodong.shi@anu.edu.au.",
     "Research School of Engineering, Australian National University, Canberra, ACT, 0200, Australia."],
 "model" : {
    "pickled_vectorizer" : *VECTORIZER*,
    "pickled_model" : *MODEL*,
    "f1_score" : 99.761,
    "precision" : 99.78,
    "recall" : 99.743,
    "accuracy" : 99.765,
    "training_date" : "2020-04-01"}
}
  ```
  
</p>
</details>

## Running

```bash
python extract.py
```

This prototype will, from a file containing a list of PMIDs, match every affiliations to the best ROR ID possible. 
The basic use will be to provide a list of PMIDs, then the prototype will return a file with every affiliation from those PMIDs tagged with the predicted ROR IDs. The file will be a table looking like the following :

<details><summary>Table preview</summary>
<p>

| PMID     | PMCID      | DOI                    | fullName   | firstName | lastName | initials | AFF                                                                                                                             | Best_name                                 | ROR_ID                    | Country        | City    | Predict                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|----------|------------|------------------------|------------|-----------|----------|----------|---------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|---------------------------|----------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 32780931 |            | 10.1002/anie.202008622 | Tosha T    | Takehiko  | Tosha    | T        | RIKEN Spring 8, RIKEN Spring 8, JAPAN.                                                                                          | RIKEN                                     | https://ror.org/01sjwvz98 | Japan          | Wako    | [{'name': 'RIKEN', 'id': 'https://ror.org/01sjwvz98', 'choose': False, 'score': 0.85, 'method': 'Prediction', 'city': 'Wako', 'country': 'Japan', 'string': 'RIKEN Spring 8, RIKEN Spring 8, JAPAN.', 'ROR_API': True, 'ROR_API_score': 1.0, 'avg': 0.92}]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 32775148 | PMC7404179 | 10.1002/advs.201903441 | Matousek P | Pavel     | Matousek | P        | Central Laser Facility STFC Rutherford Appleton Laboratory Oxford OX11 0QX UK.                                                  | Science and Technology Facilities Council | https://ror.org/057g20z61 | United_Kingdom | Swindon | [{'name': 'Science and Technology Facilities Council', 'id': 'https://ror.org/057g20z61', 'choose': True, 'score': 1.0, 'method': "Acronyms : 'STFC'", 'city': 'Swindon', 'country': 'United_Kingdom', 'string': 'Central Laser Facility STFC Rutherford Appleton Laboratory Oxford OX11 0QX UK.', 'ROR_API': True, 'ROR_API_score': 1.0, 'avg': 1.0}]                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 32812294 |            | 10.1002/adma.202003003 | Guang Y    | Yao       | Guang    | Y        | Center of Materials Science and Optoelectronics Engineering, University of Chinese Academy of Sciences, Beijing, 100049, China. | University of Chinese Academy of Sciences | https://ror.org/05qbk4x57 | China          | Beijing | [{'name': 'Chinese Academy of Sciences', 'id': 'https://ror.org/034t30j35', 'choose': True, 'score': 1.0, 'method': "Exact match : 'Chinese Academy of Sciences' Beijing China", 'city': 'Beijing', 'country': 'China', 'string': 'Center of Materials Science and Optoelectronics Engineering, University of Chinese Academy of Sciences, Beijing, 100049, China.'}, {'name': 'University of Chinese Academy of Sciences', 'id': 'https://ror.org/05qbk4x57', 'choose': True, 'score': 1.0, 'method': "Exact match : 'University of Chinese Academy of Sciences' Beijing China", 'city': 'Beijing', 'country': 'China', 'string': 'Center of Materials Science and Optoelectronics Engineering, University of Chinese Academy of Sciences, Beijing, 100049, China.'}] |

</p>
</details>

## Details

### extract
This file contains all algorithms needed to match ROR IDs to affiliation.

The most important are : 

<details><summary><b><i>is_ORG(request,ORG,city="",country="",proba=False)</i></b></summary>
<p>
  - <b>Description :</b> This function based on affiliation and an organization will return a predicted response. To be able to make an exact match of the institution name, country and city, matched location are required.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>request :</i> It is a string corresponding to an affiliation.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>ORG :</i> A dictionary based on the format of each organization in the MongoDB collection (see in Introduction).<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>city :</i> A city (string) matched in the affiliation and existing in the MongoDB collection.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>country :</i> A country (string) matched in the affiliation and existing in the MongoDB collection.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>proba :</i> A boolean that indicate to the algorithm if it needs to return the probability(or prediction score) or not.<br>
    - <b>Return :</b> It will return a dictionary with all following information to be able to understand the prediction.<br>
 <details><summary>Response exemple</summary>
    <p>
      
    {
      "name" : 'Chinese Academy of Sciences',
      "id" : 'https://ror.org/034t30j35',
      "choose" : True,
      "score" : 1.0,
      "method" : "Exact match : 'Chinese Academy of Sciences' Beijing China",
      "city" : "Beijing",
      "country" : "China",
      "string" : 'Center of Materials Science and Optoelectronics Engineering, University of Chinese Academy of Sciences, Beijing, 100049, China.'
      }
      
   </p>
  </details>
</p>
</details>

<details><summary><b><i>get_ROR(affiliation,treshold=0.7)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will try to match in the whole MongoDB collection the best organizations. Thus it will search geolocation information (weak spot of the algorithm, as it takes a long time), based on pre-built Geonames dictionaries. And then predict on selected institutions.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>affiliation :</i> It is a string corresponding to an affiliation.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>treshold :</i> Score below which insitution will not be matched.<br>
  - <b>Return :</b> It will return a list of dictionaries of each institution with a prediction score superior to the treshold and ordered from the worst to best match based on the prediction score (sometime score sometimes avg, it depends if the algorithm needs to make a request to the ROR API). The response will be a list of dictionaries like the response of <b>is_ORG()</b>.<br>
</p>
</details>


<details><summary><b><i>tag_PMIDs(PMIDs_file="test.csv",resultfile="test.tsv",no_duplicates=False)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will try to match every affiliation in a set of PMIDs provide in the entry file.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>PMIDs_file :</i> A path to a csv or txt file containing a list of PMIDs. It can also be the list of PMIDs passed as a string.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>resultfile :</i> A path  and a filename for the resulting file.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>no_duplicates :</i> A boolean to have all affiliations tagged or just the unique affiliations in the resulting file.<br>
  - <b>Return :</b> The result will be the same table (a tsv file) as demonstrate in the Running part.<br>
</p>
</details>


This file also contains a class called Pretty which could be used in a Jupyter notebook for example with basic algorithms :

<details><summary><b><i>Pretty.get_ROR()</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will ask the user to enter manually a string of his choice and thenit will try to assign the best institution based on the get_ROR function detailed above. It will then print the result in a friendly way.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;None.<br>
  - <b>Return :</b> None.<br>
</p>
</details>

<details><summary><b><i>Pretty.PMID_to_ROR()</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will ask the user to enter manually a PMID in the following format "PMID:XXXXXXX", then algorrithm will process the PMID and plot a map of author collaboration in this publication. It will also produce a bar chart about the country frequency collaboration. Those plot will be in the form of two html files which should open automatically at the end of the process.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;None.<br>
  - <b>Return :</b> None.<br>
</p>
</details>

<details><summary><b><i>Pretty.ROR_API_call(best=True)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will ask the user to enter a string corresponding to an author affiliation. It will then make a request to the ROR API and print the best result or the whole response<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>best :</i> A boolean to ask forone organization in the response or the whole response.<br>
  - <b>Return :</b> A dictionary corresponding to one organization or the whole response of the ROR API.<br>
</p>
</details>



### manage
Or manage_db. This file contains all algorithms needed to manage the MongoDB collection.

```
python manage_db.py https://ror.org/034t30j35
```

Running it with a ROR ID as argument will make the script trying to fill the dataset of affiliation for this organization with at least 1000 affiliations found by exact match within Europe PMC.

```
python manage_db.py Finland
```

Running it with a country name as argument will make the script trying to fill the dataset of affiliation for all organization within the country with at least 100 affiliations found by exact match within Europe PMC.

Here are the most important algorithms in this file :

<details><summary><b><i>get_stats(types=False,status=False,country=False,city=False,list_aff=False,model=False,save=False)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will collect the data necessary to have basic statistics on the MongoDB collection and return it as a response.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>types :</i> A boolean to get or not institution types statistics.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>status :</i> A boolean to get or not institution status statistics.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>country :</i> A boolean to get or not countries statistics (number of institutions in a country).<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>city :</i> A boolean to get or not cities statistics (number of institutions in a city).<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>list_aff :</i> A boolean to get or not "list_aff" statistics (affiliation datasets for each organizations).<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>model :</i> A boolean to get or not model statistics (number of models trained and performances).<br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>save :</i> A boolean to save or just return the results.<br>
  - <b>Return :</b> The result will be a list of dictionaries in case save is set to False or a list of file based on the statistics asked.<br>
  <details><summary>Response exemple</summary>
      <p>
      
    [
    { # Types #
      "Company":2000,
      "Education":300
    },
    { # Status #
      "Active":45085
    },
    { # Country #
      "United_States":45085,
      "United_Kingdom":54126,
      "Germany":5455
    },
    { # City #
      "London":485,
      "New_York":526,
      "Caen":55
    },
    { # list_aff #
      "with_affs":485,
      "without_affs":526,
      "distribution":
      {
          5460:2,
          56850:63,
          1:1000,
      }
    },
    { # Models #
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
    ]
      
   </p>
  </details>
  
</p>
</details>



<details><summary><b><i>train_ROR(ROR_ID)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will try to train the model, based on affiliations collected in the MongoDB collection, corresponding to the ROR ID provided.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>ROR_ID :</i> A string corresponding to the ROR_ID of the institution you want to "train".<br>
  - <b>Return :</b> None or False if there is not enough affiliations to train the model (either "False" or "True" affiliations.<br>
</p>
</details>

<details><summary><b><i>train_all(new=False,date="2020-05-29")</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will try to train a model for all organizations.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>new :</i> A boolean to indicate if the user want to train only the "new" models or not. Here, "new" models corresponds to institutions with enough affiliations in both "True" and "False" dataset to be trained but the model has not been trained yet. <br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>date :</i> A string in the following format : "YYYY-MM-DD", this date will be used to train only older models than this date. It is recommanded to use the date when you launch the training.<br>
  - <b>Return :</b> None.<br>
</p>
</details>

<details><summary><b><i>predict_ROR(ROR_ID,affiliation)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm will use the model of the corresponding ROR ID to predict on the affiliation provided. It is a simple algorithm only using ML to match the organization.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>ROR_ID :</i> A string corresponding to the ROR_ID of the institution you want to match to the affiliation. <br>
  &nbsp;&nbsp;&nbsp;&nbsp;-  <i>affiliation :</i> A string corresponding to an author affiliation.<br>
  - <b>Return :</b> It will return the prediction score.<br>
</p>
</details>


To update the database with ROR release three different algorithms are needed however the ***update_collection()*** algorithm will process the whole update  :

<details><summary><b><i>update_collection(rorapi_directory="ror-api/",filename="dictio_C_c_ROR.json",update_directory="./update_dir/",collect=True,train=True,clean=True)</i></b></summary>
<p>
  - <b>Description :</b> This function will pull an update from the ROR API's github, then match cities from GRID, update the MongoDB collection, makes searches for 'new' institutions in the collection and thus fill with unique affiliations there datasets. In the end if there are enough data, the algorithm will train the new models.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>rorapi_directory :</i>Name of the ROR API directory used to pull from GitHub.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>filename :</i>Name of the file resulting from the match of cities from GRID.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>update_directory :</i>Path of the update directory where all files needed will be generated.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>collect :</i>A boolean to indicate if you want to collect unique affiliations for the new ROR records.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>train :</i>A boolean to indicate if you want to train the new ROR records with the unique affiliations collected.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>clean :</i>A boolean to indicate if you want to clean your machine from all the files used during the process.<br>
  - <b>Return :</b> It will return the list of new ROR IDs added to the Mongo DB collection.<br>
</p>
</details>


<details><summary><b><i>update_ror_json(rorapi_directory="ror-api/",update_directory="./update_dir/")</i></b></summary>
<p>
  - <b>Description :</b> To run this algorithm it is necessary to clone the ROR API github on your machine and provide the ROR API folder path at the begining of the script. This step will pull the ROR API github repository. and unzip the last update of the ROR database.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>rorapi_directory :</i>Name of the ROR API directory used to pull from GitHub.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>update_directory :</i>Path of the update directory where all files needed will be generated.<br>
  - <b>Return :</b> None.<br>
</p>
</details>


<details><summary><b><i>build_ROR_GRID_json(filename="dictio_C_c_ROR.json",update_directory="./update_dir/")</i></b></summary>
<p>
  - <b>Description :</b> To run this algorithm it is necessary to have two file the ror.json from the update_ror_json() and the grid.csv, which can be obtain directly from GRID. This algorithm will match cities and countries to their corresponding ROR ID. In the end it will be the same structure as the ROR database but with supplementary field : city.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>filename :</i>Name of the file resulting from the match of cities from GRID.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>update_directory :</i>Path of the update directory where all files needed will be generated.<br>
  - <b>Return :</b> None.<br>
</p>
</details>

<details><summary><b><i>refresh_MongoDB(filename="dictio_C_c_ROR.json",update_directory="./update_dir/",collect=True,train=True)</i></b></summary>
<p>
  - <b>Description :</b> To run this algorithm it is necessary to have the json file provide by the function build_ROR_GRID_json(). This algorithm will update the MongoDB collection with the new organizations registered by ROR in the last update.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>filename :</i>Name of the file resulting from the match of cities from GRID.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>update_directory :</i>Path of the update directory where all files needed will be generated.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>collect :</i>A boolean to indicate if you want to collect unique affiliations for the new ROR records.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>train :</i>A boolean to indicate if you want to train the new ROR records with the unique affiliations collected.<br>
  - <b>Return :</b> List of new ROR IDs added to the MongoDB collection.<br>
</p>
</details>

### mapping
This file contains the algorithm necessary to plot a map from a dictionary of countries with their corresponding count.

<details><summary><b><i>map_display(search_title,country_dict,)</i></b></summary>
<p>
  - <b>Description :</b> This algorithm is used to produced two plot, one map and one barplot from a country frequency dictionary. This algorithm is mostly used for a visualisation in the class Pretty in the <i>extract</i> file.<br>
  - <b>Args :</b><br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>search_title :</i> A string which will corresponds to plot titles.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;- <i>country_dict :</i> A country frequency dictionary.<br>
  - <b>Return :</b> None.<br>
</p>
</details>
