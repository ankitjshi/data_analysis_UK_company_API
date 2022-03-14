# list of library used in this project
# ! pip install pgeocode
# ! pip install plotly
# ! pip install gender_guesser
import json
import time
from time import sleep
import requests
from datetime import datetime
from datetime import date
import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
import pgeocode
import plotly.express as px
import pandas as pd
import gender_guesser.detector as gender
from cycler import cycler

# Data Analysis Steps followed:
# Step 1: Data Collection and Class Creations
# Step 2: Data Merging and manipunation
# Step 3: Data Analysis and Visualization

# ===========================================
# Step 1: Data Collection and Class Creations
# Step 2: Data Merging and manipunation
# ===========================================

# Seperate Companylist class holds information of list of companies, list of company numbers and keyword sector
# for which the analysis is performed, it basically captures the details from the search API
# on initialization it needs above infromation, seperate list of persons relevant to sectors and updation of company list fetching information from company api is done
class CompanyList:
    def __init__(self, company_list, company_numbers, sector):
        self.company_list = company_list
        self.company_numbers = company_numbers
        self.sector = sector

    def add_persons_with_control(self, persons):
        self.persons = persons

    def update_company_list(self,company_list):
        self.company_list = company_list

    def add_location_informations(self,location_df):
        self.location_df = location_df

# Seperate Company class holds information of company from the company API,
# It holds information of single company like status, date of creation, cessation, insolvency, liquidation and charges
class Company:
  def __init__(self, company_number):
    self.company_number = company_number

  def add_status_and_dates(self, status, date_of_creation, date_of_cessation):
    self.status = status
    self.date_of_creation = date_of_creation
    self.date_of_cessation = date_of_cessation

  def add_other_informations(self,insolvency,liquidation,charges):
    self.insolvency = insolvency
    self.liquidation = liquidation
    self.charges = charges

# Seperate PersonWithControl class holds information from API persons_of_significant_control,
# It holds information of person's name, calcuated age, gender and nature of their control
class PersonWithControl:
  def __init__(self, name, age, nature_of_control, gender):
    self.name = name
    self.age = age
    self.nature_of_control = nature_of_control
    self.gender = gender

# Function calculates the gender based on the title of title is uncertain like Dr or not present
# a call to another method is made to fetch gender
def fetch_gender(name):
    if ('Mrs' not in name) and ('Mr' in name or 'Mister' in name):
        return 'male'
    elif 'Mrs' in name or 'Ms' in name or 'Miss' in name:
        return 'female'
    else:
        return gender_guessor(name)

# A new method is added to guess the gender of the person based on its first name,
# it has pre built database of names classified and helps us to some extent where we dont see titles
def gender_guessor(name):
    d = gender.Detector()
    name = name.replace('Dr ','').replace('.','')
    first_name = name.split(' ')[0]
    if first_name == "":
        first_name = name.split(' ')[1]
    gd = d.get_gender(first_name)
    gendr = gd.replace('mostly_','')
    return gendr

# saves data in file
def save_data_as_file(data, file_name):
    with open(file_name, 'w') as outfile:  # 'w' means open for writing.
        json.dump(data, outfile)

# Establish connection with the main API with the timeout if needed, the compnay key token is passed to fetch the information
# It times out after few limits so a timeout of 5 minute is needed, it designed with temporary timeput of 5s
def call_api_with(url_extension):
    your_company_house_api_key = "97497785-82d4-4f7f-9c40-96598f92d987"
    login_headers = {"Authorization": your_company_house_api_key}
    url = f"https://api.companieshouse.gov.uk/{url_extension}"
    res = requests.get(url, headers=login_headers)  # , verify=False)
    if res.status_code != 200:
        time.sleep(5)
        res = requests.get(url, headers=login_headers)  # , verify=False)
    return res.json()

# Funtion to fetch list of all companies based on specific keyword, it has an output for number of countries if its more than 100 we use pagination approch
def search_for_companies_with_query(query, number_of_companies=500):
    if number_of_companies < 100:
        url = f"search/companies?q={query}&items_per_page={number_of_companies}"
        return call_api_with(url).get('items', [])
    else:
        page_size = 100
        number_of_pages = math.ceil(number_of_companies / page_size)  # round up
        companies = []
        for page_index in range(0, number_of_pages):
            url = f"search/companies?q={query}&items_per_page={page_size}&start_index={page_index * page_size}"
            companies += call_api_with(url).get('items', [])
        return companies


# function for searching the list of companies based on query to retrieve JSON
def search_for_disolvedcompanies_with_query(query, number_of_companies=500):
    if number_of_companies < 100:
        url = f"search/dissolved-search?q={query}&search_type=best-match&items_per_page={number_of_companies}"
        return call_api_with(url).get('items', [])
    else:
        page_size = 100
        number_of_pages = math.ceil(number_of_companies / page_size)  # round up
        companies = []
        for page_index in range(0, number_of_pages):
            url = f"search/dissolved-search?q={query}&search_type=best-match&items_per_page={page_size}&start_index={page_index * page_size}"
            companies += call_api_with(url).get('items', [])
        return companies


# request to get company data based on company number
def data_for_company(company_number):
    url = f"company/{company_number}"
    return call_api_with(url)


# get all officers from a company based on company number
def all_officers_in_company(company_number):
    url = f"company/{company_number}/officers"
    return call_api_with(url).get('items', [])

# get all persons from a company based on company number
def all_persons_in_company(company_number):
    url = f"company/{company_number}/persons"
    return call_api_with(url).get('items', [])

# get all persons with significant control from a company based on company number
def person_with_control(company_number):
    url = f"company/{company_number}/persons-with-significant-control"
    sleep(0.1)
    return call_api_with(url).get('items', [])

# ====================================================
# Information Retrival for Part 1
# ====================================================

# Function calculates the age of the person based on the birth information and current day
def calculate_age(date_of_birth):
    if (date_of_birth.get('month') is None or date_of_birth.get('year') is None):
        return
    birth_month=date_of_birth.get('month')
    birth_year=date_of_birth.get('year')
    today = date.today()
    return today.year - birth_year - ((today.month, today.day) < (birth_month, today.day))

# Its used to solve the first Business question
# Function makes a call to person_with_control api and gets repective list per company number
# It then makes a call to fetch_gender,calculate_age and stores its information into perosn object
# all the objects are then passed as list for easier visualization
def fetch_person_with_control(company_numbers):
    personwithcontrolList = []
    for company_number in company_numbers:
        allpersonswithcontrol = person_with_control(company_number)
        age = None
        for person in allpersonswithcontrol:
            name = person.get('name')
            if 'Ltd' in name or 'Limited' in name:
                continue
            if person.get('natures_of_control') is not None:
                nature_of_control = person.get('natures_of_control')
            gender = fetch_gender(name)
            if person.get('date_of_birth') is not None and gender=='female':
                age = calculate_age(person.get('date_of_birth'))
            personwithcontrolList.append(PersonWithControl(name, age, nature_of_control, gender))
    return personwithcontrolList

# Its used to solve the first Business question
# Function makes a call to search_for_companies_with_query api and fetch_person_with_control mentioned above
# It stores list of person objects into Companylist object
# The purpose is to have all information in one place
def fetch_company_information_for_persons(keyword,numOfComp):
    print("Fetching Compamny Information for the sector: "+keyword)
    companyList = search_for_companies_with_query(keyword, numOfComp)
    compNumList = [company.get('company_number') for company in companyList]
    print("Fetching Person Information for the sector: "+keyword)
    personsList = fetch_person_with_control(compNumList)
    compListObj = CompanyList(companyList, compNumList, keyword)
    compListObj.add_persons_with_control(personsList)
    print("Information Fetched Successfully for the sector: "+keyword)
    print("============================================")
    return compListObj

# ====================================================
# Information Retrival for Part 2
# ====================================================
# Function makes a call to pgeocode api and fetches lattitude longitude information based on its postal code
# A new data_frame is returned which has list of lattitude/longitude/postal code information as its tupples
def fetch_location_information(companyList,keyword):
    lattitude=[]
    longitude=[]
    postalCode=[]
    for company in companyList:
        regOffAdd = company.get('address')
        if regOffAdd is not None and regOffAdd.get('postal_code') != '':
            if regOffAdd.get('postal_code') is not None:
                nomi = pgeocode.Nominatim('gb')
                postal_code = regOffAdd.get('postal_code')
                postalCode.append(postal_code)
                location = nomi.query_postal_code(postal_code)
                lattitude.append(location.latitude)
                longitude.append(location.longitude)

    list_of_tuples = list(zip(postalCode, lattitude, longitude))
    df_comp = pd.DataFrame(list_of_tuples,
                           columns=['postalCode', 'latitude', 'longitude'])
    df_comp['Sector_Type'] = keyword
    df_comp['latitude'].apply(lambda x: float(x))
    df_comp['longitude'].apply(lambda x: float(x))
    df_comp = df_comp.dropna()
    return df_comp

# Its used to solve the Second Business question
# Function makes a call to search_for_companies_with_query api and gets repective list per company number
# It then makes a call fetch_location_information for fetching location information per company
# All of which is stored in company_list object
def fetch_various_companies(keyword,numOfComp):
    print("Fetching Compamny Information for the sector: "+keyword)
    companyList = search_for_companies_with_query(keyword, numOfComp)
    compNumList = [company.get('company_number') for company in companyList]
    print("Fetching Companies Information for the sector: "+keyword)
    compListObj = CompanyList(companyList, compNumList, keyword)
    df_comp = fetch_location_information(companyList,keyword)
    compListObj.add_location_informations(df_comp)
    # compListObj = fetch_companies_other_information(companyList, compListObj)
    print("Information Fetched Successfully for the sector: "+keyword)
    print("============================================")
    return compListObj

# ====================================================
# Information Retrival for Part 3
# ====================================================
# Its used to solve the Third Business question
# Function makes a call to company api and gets repective information of each company per company number
# It then makes gets important attributes like company_status/creation-date/cessation-date/insolvancy/charges/liquidation histories
# All of which is stored in company object
def fetch_companies_other_information(compNumList,compListObj):
    compList = []
    for com_number in compNumList:
        data = data_for_company(com_number)
        status = data.get('company_status')
        creation = data.get('date_of_creation')
        cessation = data.get('date_of_cessation')

        insolvency = data.get('has_insolvency_history')
        liquidation = data.get('has_been_liquidated')
        charges = data.get('has_charges')
        file = data.get('can_file')
        compObj = Company(com_number)
        compObj.add_status_and_dates(status,creation,cessation)
        compObj.add_other_informations(insolvency,liquidation,charges)
        compList.append(compObj)

    compListObj.update_company_list(compList)
    return compListObj

# ===========================================
# Step 2: Data Merging and manipunation
# Step 3: Data Analysis and Visualization
# ===========================================

# Function helps to get respective counts of male/female and unknowns per sector from the objects
def tune_gender_info(sectorList):
    visualize_list=[]
    for sector in sectorList:
        gender_info = {}
        maleCount = len(list(filter(lambda x: x.gender == 'male', sector.persons)))
        femaleCount = len(list(filter(lambda x: x.gender == 'female', sector.persons)))
        unknownCount = len(list(filter(lambda x: x.gender == 'unknown', sector.persons)))
        gender_info['maleCount'] = maleCount
        gender_info['femaleCount'] = femaleCount
        gender_info['unknownCount'] = unknownCount
        gender_info['sector'] = sector.sector
        print(gender_info)
        visualize_list.append(gender_info)
    return visualize_list

# Function helps to get age groups based on the age counts received for all the women in top hierarchy
def prepare_age_groupings(ageList):
    age_group_dict = {'20-30': 0, '30-40': 0, '40-50': 0, '50-60': 0, '60-70': 0, '70-80': 0}
    for age in ageList:
        if age > 20 and age <= 30:
            age_group_dict['20-30'] = age_group_dict.get('20-30')+1
        elif age > 30 and age <= 40:
            age_group_dict['30-40'] = age_group_dict.get('30-40')+1
        elif age > 40 and age <= 50:
            age_group_dict['40-50'] = age_group_dict.get('40-50')+1
        elif age > 50 and age <= 60:
            age_group_dict['50-60'] = age_group_dict.get('50-60')+1
        elif age > 60 and age <= 70:
            age_group_dict['60-70'] = age_group_dict.get('60-70')+1
    return age_group_dict

# It gets the nature_of_control for male and female seperately per sector
def extract_owner_list(sectorList):
    gender_based_ownership = {}
    male_list=[]
    female_list=[]
    for sector in sectorList:
        for person in sector.persons:
            if person.gender == 'male':
                male_list.append(person.nature_of_control)
            elif person.gender == 'female':
                female_list.append(person.nature_of_control)
    flat_male_list = [item for sublist in male_list for item in sublist]
    flat_female_ist = [item for sublist in female_list for item in sublist]
    gender_based_ownership['male']=flat_male_list
    gender_based_ownership['female']=flat_female_ist
    return gender_based_ownership

# It filters the list and gets the counts of each ownership info
def extract_ownership_counts(final_list):
    count_list={}
    for ownerinfo in set(final_list):
        ownershipCount = len(list(filter(lambda x: x==ownerinfo, final_list)))
        count_list[ownerinfo]=ownershipCount
    return count_list

# Out of numerous ownership info 4 groups are classifed for ease of better visualization and deeper insights
def create_ownership_groups(countlist):
    ownership_dict={'voting-rights':0,'ownership-of-shares':0,'right-to-appoint':0,'significant-influence':0}
    for key in countlist:
        if 'voting-rights' in key:
            ownership_dict['voting-rights']=ownership_dict.get('voting-rights')+1
        elif 'ownership-of-shares' in key:
            ownership_dict['ownership-of-shares']=ownership_dict.get('ownership-of-shares')+1
        elif 'right-to-appoint' in key:
            ownership_dict['right-to-appoint']=ownership_dict.get('right-to-appoint')+1
        elif 'significant-influence' in key:
            ownership_dict['significant-influence']=ownership_dict.get('significant-influence')+1
    return ownership_dict

# Plots respective part charts for male and females for various sectors
def plot_pie_charts(labels,sizes,topic):
    plt.figure(figsize=(18, 5.5))
    colors = plt.cm.ocean_r(np.linspace(0.2, 0.8, 5))
    plt.rcParams['axes.prop_cycle'] = cycler(color=colors)
    # plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    labels = [f'{l}, {s:0.1f}' for l, s in zip(labels, sorted(labels, reverse=True))]
    patches, texts = plt.pie(sizes, startangle=90, labels=labels)
    plt.legend(patches, labels, loc="center right", prop={'size': 8})
    plt.axis('equal')
    plt.title('Distribution of Ownership rights -'+topic)
    plt.show()

# ====================================================
# Visualization for Part 1
# ====================================================

# This method helps to visualize gender diversity across top two sectors entertainment and healthcare
# It first analyses the data and get relevant counts and then proceeds for plt visualization
def visualize_gender_diversity(sectorList):
    visualize_list = tune_gender_info(sectorList)
    print('visualize_list:',visualize_list)
    sectorList = [info.get('sector') for info in visualize_list]
    maleCountList = [info.get('maleCount') for info in visualize_list]
    femaleCountList = [info.get('femaleCount') for info in visualize_list]
    unknownCountList = [info.get('unknownCount') for info in visualize_list]

    plt.figure(figsize=(20, 10))
    ax = sns.barplot(y=maleCountList, x=sectorList, color="gray", label="males")
    ax = sns.barplot(y=femaleCountList, x=sectorList, color="navy", label="females")
    ax = sns.barplot(y=unknownCountList, x=sectorList, color="black", label="unknowns")
    ax.legend(loc='upper right', prop={'size': 9})

    def change_width(ax, new_value):
        for patch in ax.patches:
            current_width = patch.get_width()
            diff = current_width - new_value
            # we change the bar width
            patch.set_width(new_value)
            # we recenter the bar
            patch.set_x(patch.get_x() + diff * .5)
    change_width(ax, .15)
    ax.set_ylabel('Total Counts', fontweight='bold', fontsize=10, labelpad=20)
    ax.set_xlabel('Sectors', fontweight='bold', fontsize=10, labelpad=20)
    plt.title("Gender wise distribution - Entertainment vs Healthcare", pad=20)
    plt.show()

# This method helps to visualize ownership information for women across top two sectors entertainment and healthcare
# It first analyses the data and get relevant counts/groups and then proceeds for plt visualization
def visualize_ownership_info(sectorList):
    gender_based_ownership = extract_owner_list(sectorList)
    male_count_list = extract_ownership_counts(gender_based_ownership.get('male'))
    female_count_list = extract_ownership_counts(gender_based_ownership.get('female'))
    males = create_ownership_groups(male_count_list)
    females = create_ownership_groups(female_count_list)
    labels = [key for key in males.keys()]
    sizes = [val for val in males.values()]
    plot_pie_charts(labels,sizes,'Males')

    labels = [key for key in females.keys()]
    sizes = [val for val in females.values()]
    plot_pie_charts(labels,sizes,'Females')

# This visualization helps to plot age distribution across all the sectors for women on top position.
# It first analyses the data and get relevant counts and age-groups
# proceeds for plt visualization later
def visualize_age_distribution(sectorList):
    age_groups = {}
    for sector in sectorList:
        sec = sector.sector
        ageList = [info.age for info in sector.persons if info.age is not None]
        groupings = prepare_age_groupings(ageList)
        age_groups[sec] = groupings

    entertainment_key = age_groups.get('entertainment').keys()
    entertainment_val = [val for val in age_groups.get('entertainment').values()]
    multimedia_val = [val for val in age_groups.get('multimedia').values()]
    music_val = [val for val in age_groups.get('music').values()]
    healthcare_val = age_groups.get('healthcare').values()
    hospital_val = age_groups.get('hospital').values()
    psychology_val = age_groups.get('psychology').values()

    plt.figure(figsize=(30, 8))
    barWidth = 0.1
    positions = np.arange(len(entertainment_key))
    plt.plot(positions + barWidth * 2, entertainment_val, 'x--', color="black", alpha=0.8, label='Entertainment-Sector')
    plt.plot(positions + barWidth * 2, multimedia_val, 'x--', color="red", alpha=0.5, label='Multimedia-Sector')
    plt.plot(positions + barWidth * 2, music_val, 'x--', color="blue", alpha=0.5, label='Music-Sector')
    plt.bar(positions + barWidth, healthcare_val, color="black", alpha=0.8, label='Healthcare-Sector', width=0.1)
    plt.bar(positions + barWidth * 2, hospital_val, color="gray", alpha=0.8, label='Hospital-Sector', width=0.1)
    plt.bar(positions + barWidth * 3, psychology_val, color="maroon", alpha=0.9, label='Psycology-Sector', width=0.1)
    plt.xlabel('Different Age Groups(in years)', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of companies', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.2, max(positions) + 1, 1.0), labels=entertainment_key)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.title('Distribution of womens age at high power across Healthcare and Entertainent sectors', fontweight='bold',
              fontsize=10)
    plt.show()

# ====================================================
# Visualization for Part 2
# ====================================================

# Function to create respective year-groups based on its value across sectors
def create_year_grouping(yearList):
    year_group_dict={'1990_1995':0,'1995_2000':0,'2000_2005':0,'2005_2010':0,'2010_2015':0,'2015_2020':0}
    for year in yearList:
        if year > 1990 and year < 1995:
            year_group_dict['1990_1995']+=1
        elif year > 1995 and year < 2000:
            year_group_dict['1995_2000']+=1
        elif year > 2000 and year < 2005:
            year_group_dict['2000_2005']+=1
        elif year > 2005 and year < 2010:
            year_group_dict['2005_2010']+=1
        elif year > 2010 and year < 2015:
            year_group_dict['2010_2015']+=1
        elif year > 2015 and year < 2020:
            year_group_dict['2015_2020']+=1
    return year_group_dict

# Function to get informarion of creation dates
def fetch_year_of_creation_list(sectorList):
    sector_yr_list = {}
    for sector in sectorList:
        sec = sector.sector
        yearList = [int(company.get('date_of_creation').split('-')[0]) for company in sector.company_list if company.get('company_status') == 'active']
        groupings = create_year_grouping(yearList)
        sector_yr_list[sec]=groupings
    return sector_yr_list

# Function to create respective age-groups based on the survival information for disolved companies
def prepare_age_groupings_services(ageList):
    age_group_dict = {'1-5': 0, '5-10': 0, '10-15': 0, '15-20': 0, '20-25': 0}
    for age in ageList:
        if age > 1 and age <= 5:
            age_group_dict['1-5'] = age_group_dict.get('1-5')+1
        elif age > 5 and age <= 10:
            age_group_dict['5-10'] = age_group_dict.get('5-10')+1
        elif age > 10 and age <= 15:
            age_group_dict['10-15'] = age_group_dict.get('10-15')+1
        elif age > 15 and age <= 20:
            age_group_dict['15-20'] = age_group_dict.get('15-20')+1
        elif age > 20 and age <= 25:
            age_group_dict['20-25'] = age_group_dict.get('20-25')+1
    return age_group_dict

# Function to get disolved comanpies, calculate its survival age and then create groups
def fetch_disolved_companies_age(sectorList):
    sector_wise_age={}
    for sector in sectorList:
        ageList = []
        sec = sector.sector
        for company in sector.company_list:
            if company.get('company_status') == 'dissolved':
                if company.get('date_of_cessation') is None or company.get('date_of_creation')is None:
                    continue
                else:
                    cessation_date = datetime.strptime(company.get('date_of_cessation'), '%Y-%m-%d')
                    creation_date = datetime.strptime(company.get('date_of_creation'), '%Y-%m-%d')
                    ageList.append(relativedelta(cessation_date, creation_date).years)
                    groups = prepare_age_groupings_services(ageList)
        sector_wise_age[sec]=groups
    return sector_wise_age

# This visualization helps to see the evolution of companies across various years
# It first analyses the data and get relevant counts and year-groups
# proceeds for plt visualization later
def visualize_evolution_of_companies(sectorList):
    year_groups = fetch_year_of_creation_list(sectorList)
    retail_key = year_groups.get('retail').keys()
    retail_val = year_groups.get('retail').values()
    hotels_val = year_groups.get('hotels').values()
    transport_val = year_groups.get('transport').values()
    vals = [val for val in year_groups.get('transport').values()]
    technology_val = year_groups.get('technology').values()
    restaurants_val = year_groups.get('restaurants').values()

    plt.figure(figsize=(20, 8))
    barWidth = 0.1
    positions = np.arange(len(retail_key))
    plt.bar(positions + barWidth, retail_val, color="mediumblue", alpha=0.8, label='Retail-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth, hotels_val, color="royalblue", alpha=0.8, label='Hotels-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth + barWidth, transport_val, color="gray", alpha=0.9,
            label='Transport-Sector', width=0.1)
    plt.plot(positions + barWidth + barWidth + barWidth, vals, 'x--', color='black', label='Service-Sector-Evolution')
    plt.bar(positions + barWidth + barWidth + barWidth + barWidth, technology_val, color="skyblue", alpha=0.8,
            label='Technology-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth + barWidth + barWidth + barWidth, restaurants_val, color="silver",
            alpha=0.8, label='Restaurants-Sector', width=0.1)
    plt.xlabel('Year Groups(in years)', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of companies', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.3, max(positions) + 1, 1.0), labels=retail_key)
    plt.legend(loc='upper left', prop={'size': 10})
    plt.title('Evolution of Service Sector Companies', fontweight='bold', fontsize=10)

    plt.show()

# This visualization helps to see the dissolved companies survival rate
# It first analyses the data and get relevant counts and age-groups
# proceeds for plt visualization later
def visualize_age_of_disolved_companies(sectorList):
    age_groups = fetch_disolved_companies_age(sectorList)
    retail_key = age_groups.get('retail').keys()
    retail_val = age_groups.get('retail').values()
    hotels_val = age_groups.get('hotels').values()
    transport_val = age_groups.get('transport').values()
    technology_val = age_groups.get('technology').values()
    restaurants_val = age_groups.get('restaurants').values()

    plt.figure(figsize=(30, 8))
    barWidth = 0.1
    positions = np.arange(len(retail_key))
    plt.bar(positions + barWidth, retail_val, color="mediumblue", alpha=0.8, label='Retail-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth, hotels_val, color="royalblue", alpha=0.8, label='Hotels-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth + barWidth, transport_val, color="gray", alpha=0.9,
            label='Transport-Sector', width=0.1)
    # plt.plot(positions + barWidth+barWidth+barWidth,vals,'x--',color='black',label='Transport-Attribute')
    plt.bar(positions + barWidth + barWidth + barWidth + barWidth, technology_val, color="skyblue", alpha=0.8,
            label='Technology-Sector', width=0.1)
    plt.bar(positions + barWidth + barWidth + barWidth + barWidth + barWidth, restaurants_val, color="silver",
            alpha=0.8, label='Restaurants-Sector', width=0.1)
    plt.xlabel('Different Age Groups(in years)', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of companies', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.3, max(positions) + 1, 1.0), labels=retail_key)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.title('Dissolved Companies Survival rate across Service Sector Companies', fontweight='bold', fontsize=10)

    plt.show()


# This visualization helps to see the geogeaphical distribution of all the companies
# It first analyses the data and get relevant counts and location-mappings
# proceeds for plt visualization later
def visualize_company_location(sectorlist):
    df_visualize = pd.DataFrame()
    for sector in sectorlist:
        df_visualize = df_visualize.append(sector.location_df, ignore_index=True)
    fig = px.scatter_mapbox(df_visualize, lat="latitude", lon="longitude", zoom=4, height=300, color="Sector_Type")
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()

# ====================================================
# Visualization for Part 3
# ====================================================


# the function fetches respective insolvency and other attributes for active vs dissolved companes
def fetch_insolvency_ration(sectorList):
    measures={}
    for sector in sectorList:
        dic_rates = {}
        sec = sector.sector
        insolvency_active = [comp.insolvency for comp in sector.company_list if comp.status =='active']
        insolvency_dissolved = [comp.insolvency for comp in sector.company_list if comp.status == 'dissolved']
        charges_active = [comp.charges for comp in sector.company_list if comp.status =='active']
        charges_dissolved = [comp.charges for comp in sector.company_list if comp.status == 'dissolved']
        liquidation_active = [comp.liquidation for comp in sector.company_list if comp.status =='active']
        liquidation_dissolved = [comp.liquidation for comp in sector.company_list if comp.status == 'dissolved']

        dic_rates['insolvency_yes_active']=insolvency_active.count(True)
        dic_rates['insolvency_no_active']=insolvency_active.count(False)
        dic_rates['insolvency_yes_dissolved']=insolvency_dissolved.count(True)
        dic_rates['insolvency_no_dissolved']=insolvency_dissolved.count(False)

        dic_rates['charges_yes_active']=charges_active.count(True)
        dic_rates['charges_no_active']=charges_active.count(False)
        dic_rates['charges_yes_dissolved']=charges_dissolved.count(True)
        dic_rates['charges_no_dissolved']=charges_dissolved.count(False)

        dic_rates['liquidation_yes_active']=liquidation_active.count(True)
        dic_rates['liquidation_no_active']=liquidation_active.count(False)
        dic_rates['liquidation_yes_dissolved']=liquidation_dissolved.count(True)
        dic_rates['liquidation_no_dissolved']=liquidation_dissolved.count(False)
        measures[sec]=dic_rates

    return measures


# This visualization helps to see the measures of insolvency and other financial attributes
# and compares them between active and dissolved companies
# It first analyses the data and get relevant counts, proceeds for plt visualization later
def visualize_insolvency_ratio(sectorList):
    keys_sect = fetch_insolvency_ration(sectorList)

    insolvency_rate = ['insolvency_yes_active', 'insolvency_no_active', 'insolvency_yes_dissolved',
                       'insolvency_no_dissolved']
    charges_rate = ['charges_yes_active', 'charges_no_active', 'charges_yes_dissolved', 'charges_no_dissolved']
    liquidation_rate = ['liquidation_yes_active', 'liquidation_no_active', 'liquidation_yes_dissolved',
                        'liquidation_no_dissolved']

    finance_insolv = [keys_sect.get('finance').get(key) for key in keys_sect.get('finance').keys() if
                      key in insolvency_rate]
    insurance_insolv = [keys_sect.get('insurance').get(key) for key in keys_sect.get('insurance').keys() if
                        key in insolvency_rate]
    realestate_insolv = [keys_sect.get('realestate').get(key) for key in keys_sect.get('realestate').keys() if
                         key in insolvency_rate]
    solicitors_insolv = [keys_sect.get('solicitors').get(key) for key in keys_sect.get('solicitors').keys() if
                         key in insolvency_rate]

    finance_charges = [keys_sect.get('finance').get(key) for key in keys_sect.get('finance').keys() if
                       key in charges_rate]
    insurance_charges = [keys_sect.get('insurance').get(key) for key in keys_sect.get('insurance').keys() if
                         key in charges_rate]
    realestate_charges = [keys_sect.get('realestate').get(key) for key in keys_sect.get('realestate').keys() if
                          key in charges_rate]
    solicitors_charges = [keys_sect.get('solicitors').get(key) for key in keys_sect.get('solicitors').keys() if
                          key in charges_rate]

    finance_liquidation = [keys_sect.get('finance').get(key) for key in keys_sect.get('finance').keys() if
                           key in liquidation_rate]
    insurance_liquidation = [keys_sect.get('insurance').get(key) for key in keys_sect.get('insurance').keys() if
                             key in liquidation_rate]
    realestate_liquidation = [keys_sect.get('realestate').get(key) for key in keys_sect.get('realestate').keys() if
                              key in liquidation_rate]
    solicitors_liquidation = [keys_sect.get('solicitors').get(key) for key in keys_sect.get('solicitors').keys() if
                              key in liquidation_rate]

    plt.figure(figsize=(30, 8))
    barWidth = 0.1
    positions = np.arange(len(insolvency_rate))
    plt.fill_between(positions + barWidth * 2, finance_insolv, color="black", alpha=0.8, label='Finance-Sector')
    plt.fill_between(positions + barWidth * 2, insurance_insolv, color="grey", alpha=0.8, label='Insurance-Sector')
    plt.fill_between(positions + barWidth * 2, realestate_insolv, color="skyblue", alpha=0.8,
                     label='Real-Estate-Sector')
    plt.fill_between(positions + barWidth * 2, solicitors_insolv, color="dodgerblue", alpha=0.8,
                     label='Solicitors-Sector')
    plt.xlabel('Measure with state yes/no for active and dissolved companies', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of insolvency', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.2, max(positions) + 1, 1.0), labels=insolvency_rate)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.title('Insolvency Rate Active vs Dissolved Companies for various sectors', fontweight='bold', fontsize=10)

    plt.figure(figsize=(30, 8))
    barWidth = 0.1
    positions = np.arange(len(charges_rate))
    plt.fill_between(positions + barWidth * 2, finance_charges, color="black", alpha=0.8, label='Finance-Sector')
    plt.fill_between(positions + barWidth * 2, insurance_charges, color="grey", alpha=0.8, label='Insurance-Sector')
    plt.fill_between(positions + barWidth * 2, realestate_charges, color="skyblue", alpha=0.8,
                     label='Real-Estate-Sector')
    plt.fill_between(positions + barWidth * 2, solicitors_charges, color="dodgerblue", alpha=0.8,
                     label='Solicitors-Sector')
    plt.xlabel('Measure with state yes/no for active and dissolved companies', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of insolvencies', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.2, max(positions) + 1, 1.0), labels=charges_rate)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.title('Charges Filed for Active vs Dissolved Companies for various sectors', fontweight='bold', fontsize=10)

    plt.figure(figsize=(30, 8))
    barWidth = 0.1
    positions = np.arange(len(liquidation_rate))
    plt.fill_between(positions + barWidth * 2, finance_liquidation, color="black", alpha=0.8, label='Finance-Sector')
    plt.fill_between(positions + barWidth * 2, insurance_liquidation, color="grey", alpha=0.8, label='Insurance-Sector')
    plt.fill_between(positions + barWidth * 2, realestate_liquidation, color="skyblue", alpha=0.8,
                     label='Real-Estate-Sector')
    plt.fill_between(positions + barWidth * 2, solicitors_liquidation, color="dodgerblue", alpha=0.8,
                     label='Solicitors-Sector')
    plt.xlabel('Measure with state yes/no for active and dissolved companies', fontweight='bold', fontsize=10)
    plt.ylabel('Total counts of liquidation', fontweight='bold', fontsize=10)
    plt.xticks(ticks=np.arange(min(positions) + 0.2, max(positions) + 1, 1.0), labels=liquidation_rate)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.title('Liquidation Rate Active vs Dissolved Companies for various sectors', fontweight='bold', fontsize=10)

print("Execution Started !!!")
print("*******************************************************")
print("If the Code Fails Please wait for 5 minutes and re-run...")

print("Fetching Compamny Information for all the Entertainment and Heatlhcare sector...")

# List of Entertainment and Healthcare sectors to visualize
sectors=['entertainment','multimedia','music','healthcare','hospital','psychology']
sectorlist=[]

# Traverse each sector and gets all the objects into list of sectors for 100 companies per sector
for sector in sectors:
    sectorlist.append(fetch_company_information_for_persons(sector, 100))
print("Proceeding for visualization...")

# Visualizes the information on the based of data captured above
visualize_gender_diversity(sectorlist)
visualize_ownership_info(sectorlist)
visualize_age_distribution(sectorlist)

print("============================================================")
print("Part 1 executed successfully")
print("============================================================")
print("Fetching Compamny Information for All the Service Sectors...")

# List of Service sectors to visualize
sectors=['retail','hotels', 'transport','technology','restaurants']
sectorlist=[]

# Traverse each sector and gets all the objects into list of sectors for 300 companies per sector
for sector in sectors:
    sectorlist.append(fetch_various_companies(sector, 300))

# Visualizes the information on the based of data captured above
visualize_evolution_of_companies(sectorlist)
visualize_age_of_disolved_companies(sectorlist)
visualize_company_location(sectorlist)

print("============================================================")
print("Part 2 executed successfully")
print("============================================================")
print("Fetching Compamny Information for all the Financial sectors...")

# List of Financial sectors to visualize
sectors=['finance','insurance', 'realestate','solicitors']
sectorlist=[]

# Traverse each sector and gets all the objects into list of sectors for 100 companies per sector
for sector in sectors:
    sectorlist.append(fetch_companies_other_information(sector, 100))

# Visualizes the information on the based of data captured above
visualize_insolvency_ratio(sectorlist)
print("============================================================")
print("Part 3 executed successfully")
print("============================================================")
print("All Execution Completed Successfully !!!...")
print("*******************************************************")
