import urllib
import requests
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import os
import html5lib
import nltk
from nltk import tokenize
from nltk.stem import PorterStemmer
import re
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time


# Add anchor tag to Job Link column in df_jobs
def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(val, val)

def classify_job_ul(job_url,ul_current_text,ul_current_str,skills_boW,responsibilities_boW,additional_boW):
    print("Inside classify_job_ul",'\n')
    df_new_cols = {}
    ul_current_str = (ul_current_str.replace('<ul>','')
     .replace('</ul>','')
     .replace('<li>','')
     .replace('</li>','')
     .replace('&amp;','')
     .replace('&amp','')
     .replace('\n',''))
    
    ul_current_str = ''.join(ul_current_str.strip())
    ul_current_str = re.sub('[^A-Za-z0-9]+', ' ', ul_current_str)
    ul_current_str = ul_current_str.lower()
    print(f"ul_current_str: {ul_current_str}\n")
    

    ul_current_tokens = nltk.word_tokenize(ul_current_str)
    ps = PorterStemmer()
    ul_current_stemmed = []
    for token in ul_current_tokens:
        ul_current_stemmed.append(ps.stem(token))

    ul_current_stemmed = set(ul_current_stemmed)
    print(f"ul_current_stemmed: {ul_current_stemmed}")
    
    skills_boW_stemmed = []
    for word in skills_boW:
        skills_boW_stemmed.append(ps.stem(word))
    
    skills_boW = set(skills_boW)
    matches_skills = len(ul_current_stemmed.intersection(skills_boW_stemmed))
    print(f"---> {matches_skills} skills matches: {ul_current_stemmed.intersection(skills_boW_stemmed)}")
    
    responsibilities_boW_stemmed = []
    for word in responsibilities_boW:
        responsibilities_boW_stemmed.append(ps.stem(word))

    responsibilities_boW_stemmed = set(responsibilities_boW_stemmed)
    matches_responsibilities = len(ul_current_stemmed.intersection(responsibilities_boW_stemmed))
    print(f"---> {matches_responsibilities} responsibilites matches: {ul_current_stemmed.intersection(responsibilities_boW_stemmed)}")
    
    additional_boW_stemmed = []
    for word in additional_boW:
        additional_boW_stemmed.append(ps.stem(word))

    additional_boW_stemmed = set(additional_boW_stemmed)
    matches_addtional = len(ul_current_stemmed.intersection(additional_boW_stemmed))
    print(f"---> {matches_addtional} additional matches: {ul_current_stemmed.intersection(additional_boW_stemmed)}")
    
    max_matches = {matches_skills:'matches_skills',
                   matches_responsibilities:'matches_responsibilities',
                   matches_addtional:'matches_addtional'}
    print(f"max_matches: {max_matches}\n")
    ul_assign_col = max_matches.get(max(max_matches))
    
    df_new_cols['Job Link'] = job_url
    if ul_assign_col == 'matches_skills':   
        df_new_cols['Skills'] = ul_current_text
    elif ul_assign_col == 'matches_responsibilities':
        df_new_cols['Responsibilities'] = ul_current_text
    elif ul_assign_col == 'matches_addtional':
        df_new_cols['Additional_Q'] = ul_current_text
    else:
        print(f'no relevant coulmn found in the current ul')
    print(f"column assigned to current ul: {df_new_cols.keys()}")
    return df_new_cols

def make_soup(driver,job_url):
    print(f"job url:{job_url}")
#     driver.implicitly_wait(5)
    driver.get(job_url) 
    html = driver.page_source
#     time.sleep(3)
    soup = BeautifulSoup(html, "html.parser")
    return soup

params = {
            'a_title' : 'job-item-title',
            'div_company_name' : 'job-item-company-name',
            'li_location' : 'job-item-location',
            'li_date' : 'job-item-timeago',
            'dl_salary' : 'job-item-salary-info',
            'a_href' : 'href',
            'job_summary':'data-offer-meta-text-snippet-link= "true"'
        }

# def load_cw_jobs_div(job_title, location,radius,postedWithin):
# First login to CW jobs to avoid access denied error
my_username = 'abhi.workk47@gmail.com'
my_password = 'Jarvis#123'

CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
CHROMEDRIVER_PATH = 'C:/Users/abhis/Documents/Study_PC/chromedriver'
WINDOW_SIZE = "1920,1080"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.binary_location = CHROME_PATH

driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                          options=chrome_options
                         )
driver.get('https://www.cwjobs.co.uk/account/signin?ReturnUrl=/')
username = driver.find_element_by_id("Form_Email")
password = driver.find_element_by_id("Form_Password")

# username.send_keys("YourUsername")
# password.send_keys("Pa55worD")
username.send_keys(my_username)
password.send_keys(my_password)

driver.find_element_by_id("btnLogin").click()
# url = (f'https://www.cwjobs.co.uk/jobs/{job_title}/in-{location}?radius={radius}&postedWithin={postedWithin}')
url = 'https://www.cwjobs.co.uk/jobs/data-scientist/in-london?radius=10&postedWithin=14'
# url = 'https://www.cwjobs.co.uk/jobs/data-scientist/in-london?radius=10'
print(f"url:{url}")

driver.get(url)
time.sleep(3)
# driver.implicitly_wait(5)

job_soup = BeautifulSoup(driver.page_source,'html.parser')
#     return soup

# For CW jobs
# Job Title
titles_list = []
for i in range(0,len(all_jobs)):
    title = all_jobs[i].find('a',{'data-at':params['a_title']}).text
    titles_list.append(title.strip())

# Company Name
company_list = []
for i in range(0,len(all_jobs)):
    company = all_jobs[i].find('div',{'data-at':params['div_company_name']}).text
    company_list.append(company)

# Link to the job
job_links = []
for i in range(0,len(all_jobs)):
    job_link = all_jobs[i].find('a',{'data-at':params['a_title']}).get('href')
    job_links.append(job_link)

# Date
job_dates = []
for i in range(0,len(all_jobs)):
    job_date = all_jobs[i].find('li',{'data-at':params['li_date']}).text
    job_dates.append(job_date.replace('Posted','Posted '))

# short Job Description
job_desc_short = []
for i in range(0,len(all_jobs)):
    job_desc_shrt = all_jobs[i].find('a',{'data-offer-meta-text-snippet-link':'true'}).text.strip()
    job_desc_short.append(job_desc_shrt)

# htmls = []
# for job_url in df_jobs['Job Link']:
#     driver.get(job_url) 
#     time.sleep(2)
#     html = driver.page_source
#     htmls.append(html)

df_jobs = pd.DataFrame(data={'Job Title': titles_list,
                             'Comapny Name':company_list,
                             'Job Link':job_links,
                             'Date Posted': job_dates,
                             'Job Summary': job_desc_short
                            })

skills_boW = ['python','statistics','sql',
              'analysis','agile','cloud','scientist','model'
              'skills','machine','deep','flask','pandas','numpy','neural'
              'tensorflow','keras','pytorch','flask','django','database','spark',
             'azure','analytics','artifical']

responsibilities_boW = ['client','project','develop','presentation','coomunication'
                        'engineers','support','experience'
                        'collaborate','partner',
                        'partners','engage','network'
                       'manage','management',
                        'deliver','deliverable','deliverables']
additional_boW = ['additionally','bonus',
                   'plus','good to have',
                   'skill','knowledge']

df_all_rows = pd.DataFrame(columns=['Skills','Responsibilities','Additional_Q']) 
for job_number in range(0,len(df_jobs['Job Link'])):
    job_url = df_jobs['Job Link'][job_number]

    job_soup = make_soup(driver,job_url)
    time.sleep(3)
    job_details = job_soup.find('div',class_='job-description')
    time.sleep(2)
#     df_job_details = pd.DataFrame(columns=['Skills','Responsibilities','Additional_Q']) 
    df_row = []
    if job_details is not None:
        for i in range(0,len(job_details.find_all('ul'))):
            ul_current_text = job_details.find_all('ul')[i].text 
            ul_current_str = str(job_details.find_all('ul')[i])
            json_out = classify_job_ul(job_url,ul_current_text,ul_current_str,skills_boW,responsibilities_boW,additional_boW)
            print(f"json_out: {json_out}")
            df_row.append(json_out)
            print(f'------------------------------- {i} ---------------------------------')

        final_json = {}
        for one_json in df_row:
            for key,value in one_json.items():
                final_json[key] = [value]

        df_row = pd.DataFrame(final_json)

        df_all_rows = pd.concat([df_all_rows,df_row])
    else:
        continue

df_all_rows.reset_index(inplace=True,drop=True)

df_final = pd.merge(df_jobs,df_all_rows,on=['Job Link'],how='outer')
df_final.fillna('',inplace=True)

df_final['Skills'] = df_final['Skills'].apply(lambda ele: '<ul>' + ''.join([f'<li>{val}</li>' if (len(val.strip()) != 0) else f'<li style="display:none;">{val}</li>' for val in ele.split('|')]) + '</ul>')

df_final['Responsibilities'] = df_final['Responsibilities'].apply(lambda ele: '<ul>' + ''.join([f'<li>{val}</li>' if (len(val.strip()) != 0) else f'<li style="display:none;">{val}</li>' for val in ele.split('|')]) + '</ul>')

df_final['Additional_Q'] = df_final['Additional_Q'].apply(lambda ele: '<ul>' + ''.join([f'<li>{val}</li>' if (len(val.strip()) != 0) else f'<li style="display:none;">{val}</li>' for val in ele.split('|')]) + '</ul>')

df_final['Job Summary'] = df_final['Job Summary'].apply(lambda ele: '<ul>' + ''.join([f'<li>{val}</li>' if (len(val.strip()) != 0) else f'<li style="display:none;">{val}</li>' for val in ele.split('|')]) + '</ul>')

div_1 = '<div style="width: 500px; height: 100px; overflow-y:scroll; vertical-align: top;">'
df_final['Job Summary'] = df_final['Job Summary'].apply(lambda val :  div_1 + val + '</div>')

df_final['Skills'] = df_final['Skills'].apply(lambda val :  div_1 + str(val) + '</div>')

df_final['Responsibilities'] = df_final['Responsibilities'].apply(lambda val :  div_1 + str(val) + '</div>')

df_final['Additional_Q'] = df_final['Additional_Q'].apply(lambda val :  div_1 + str(val) + '</div>')

div_2 = '<div style="width: 140px;height: 100px; vertical-align: top;">'
df_final['Date Posted'] = df_final['Date Posted'].apply(lambda val :  div_2 + str(val) + '</div>')
df_final['Job Title'] = df_final['Job Title'].apply(lambda val :  div_2 + str(val) + '</div>')
df_final['Comapny Name'] = df_final['Comapny Name'].apply(lambda val :  div_2 + str(val) + '</div>')

df_final_styled = (df_final.style.format({"Job Link": make_clickable}))

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/',methods=['GET','POST'])
def home():
    print("Hello")
#     return df_final_styled.hide_index().render()
    return render_template('index_bs.html',tables=[df_final_styled.hide_index().render()])
if '__main__' == __name__:
    app.run()