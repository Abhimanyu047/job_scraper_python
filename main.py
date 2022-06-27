# -------------------------------------------------------- Imports ---------------------------------------------#
import urllib
import requests
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import os
import html5lib
from nltk import tokenize
import nltk
from nltk.stem import PorterStemmer
import re
from selenium.webdriver.chrome.options import Options
from flask import Flask, render_template
# ------------------------------------------------------ Import Ends ------------------------------------------#

# --------------------------------------------------- Initializations -----------------------------------------#
# Initialize flask app
app = Flask(__name__)

# Define the Bag of words to be used to classify the job details extracted using make_job_soup function
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
# --------------------------------------------------- InitializationsEnd -----------------------------------------#

# ------------------------------------------- Function definitions Start --------------------------------------#
def load_indeed_jobs_div(job_title, location):
    '''
    Take Job Title and Location as input and Fetch jobs listed on the webpage using Beautiful Soup and requests.
    This function is used to scrape the content from the webpage and return a soup object containing the html tags.
    '''
    getVars = {'q' : job_title, 'l' : location, 'radius':'25', 'fromage' : '7','start':'0'}
    url = ('https://www.indeed.co.uk/jobs?' + urllib.parse.urlencode(getVars))
    print(f"url:{url}")
    # put the path to chromedriver
    chromedriver_path = 'C:/Users/abhis/Documents/Study_PC/chromedriver'
    driver = webdriver.Chrome(chromedriver_path) 
    driver.get(url) 
    html = driver.page_source
    soup = BeautifulSoup(html, "html5lib")
    return soup

# Add anchor tag to Job Link column in df_jobs
def make_clickable(val):
    '''
    Convert text URLs into HTML anchor tag to be used as hyperlink opening in a new tab of the browser. 
    '''
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(val, val)

def make_job_soup(job_url):
    '''
    Fetch additional details for the input Job URL and return a soup object containing the HTML tags
    '''
    print(f"job url:{job_url}")
    
    # Using chrome_options prevents the browser from loading and popping up upon using chrome driver
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
    driver.get(job_url) 
    html = driver.page_source
    soup = BeautifulSoup(html, "html5lib")
    return soup

def classify_job_ul(job_url,ul_current_text,ul_current_str,skills_boW,responsibilities_boW,additional_boW):
    '''
    Extract important details like Skills, Responsibilites, Job Summary, Date posted, etc. 
    from the job listing fetched from the Job URL.
    '''
    print("Inside classify_job_ul",'\n')

    df_new_cols = {} # contains the final classified output
   
    # Cleaning the html string for easy processing
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
    
    # tokenize the text and stem the words for easy matching with the words in the bag of words
    # This helps to cassify to which bag the all tne list elements in the <ul> belong. 
    ul_current_tokens = nltk.word_tokenize(ul_current_str)
    ps = PorterStemmer()
    ul_current_stemmed = []
    for token in ul_current_tokens:
        ul_current_stemmed.append(ps.stem(token))
    ul_current_stemmed = set(ul_current_stemmed)
    print(f"ul_current_stemmed: {ul_current_stemmed}")
    
    # Stemming the words in all the bags of words for easy matching with the html tokenized and stemmed string
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
    
    # finding the bag to which maximum words matched
    max_matches = {matches_skills:'matches_skills',
                   matches_responsibilities:'matches_responsibilities',
                   matches_addtional:'matches_addtional'}
    print(f"max_matches: {max_matches}\n")
    ul_assign_col = max_matches.get(max(max_matches))
    
    df_new_cols['Job Link'] = job_url # Just making this column for merging purposes to the parent dataframe later
    
    # Classifying and assigning the column to which the given <li> elements of the input <ul> should belong
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
# ----------------------------------------------- Function definitions end --------------------------------------------#
# ----------------------------------------------- Business Logic Starts ----------------------------------------------#
# Scrape the data from the webpage using BeautifulSoup and Requests modules
job_soup = load_indeed_jobs_div('Data Scientist','london')

# Extract Job Title from the scraped text
all_jobs = job_soup.find_all('div',class_='job_seen_beacon')
titles_list = []
for i in range(0,len(all_jobs)):
    title = all_jobs[i].find('a',class_='jcs-JobTitle').text
#     print(f"{i} -> {all_jobs[i].find('a',class_='jcs-JobTitle').text}")
    titles_list.append(title.strip())

# Extract Company Name from the scraped text
company_list = []
for i in range(0,len(all_jobs)):
    company = all_jobs[i].find('span',class_='companyName').text
#     print(f"{i} -> {all_jobs[i].find('span',class_='companyName').text}")
    company_list.append(company)

# Extract Link to the job from the scraped text
job_links = []
for i in range(0,len(all_jobs)):
    job_link = 'https://indeed.co.uk' + all_jobs[i].find('a')['href']
#     print(f"{i} -> https://indeed.co.uk{all_jobs[i].find('a')['href']}")
    job_links.append(job_link)



# Extract Date of job posting from the scraped text
job_dates = []
for i in range(0,len(all_jobs)):
    job_date = all_jobs[i].find('span',class_='date').text
#     print(f"{i} -> {all_jobs[i].find('span',class_='date').text}")
    job_dates.append(job_date.replace('Posted','Posted '))

# Extract short Job Description from the scraped text
job_desc_short = []
for i in range(0,len(all_jobs)):
    job_desc_shrt = all_jobs[i].find('div',class_='job-snippet').text.strip()
    print(f"{i} -> {all_jobs[i].find('div',class_='job-snippet').text.strip()}")
    job_desc_short.append(job_desc_shrt)

# Storing all the extracted information in a dataframe for further analysis
df_jobs = pd.DataFrame(data={'Job Title': titles_list,
                             'Comapny Name':company_list,
                             'Job Link':job_links,
                             'Date Posted': job_dates,
                             'Job Summary': job_desc_short
                            })

# Creating additional dataframe to store the information extracted using the Job URL using make_job_soup function
df_all_rows = pd.DataFrame(columns=['Skills','Responsibilities','Additional_Q']) 

# Parsing each Job link to extract additional info related to the job like Skills required, 
# Responsibilites, User Profile, etc. using various tags extracted using make_job_soup function
for job_number in range(0,len(df_jobs['Job Link'])):
    job_url = df_jobs['Job Link'][job_number]
    job_soup = make_job_soup(job_url)
    job_details = job_soup.find_all('div','jobsearch-jobDescriptionText')[0]
    df_row = [] # appending all the extracted info for one job to be added to the dataframe later
    # iterating over each <ul> tag present in the job_details soup and classifying the <ul> using clasify_job_ul()
    for i in range(0,len(job_details.find_all('ul'))):
        ul_current_text = job_details.find_all('ul')[i].text 
        ul_current_str = str(job_details.find_all('ul')[i])
        json_out = classify_job_ul(job_url,ul_current_text,ul_current_str,skills_boW,responsibilities_boW,additional_boW)
        print(f"json_out: {json_out}")
        df_row.append(json_out)
        print(f'------------------------------- {i} ---------------------------------')

    final_json = {} # To convert the <ul> data appended to df_row into a dataframe later to be merged with df_jobs
    for one_json in df_row:
        for key,value in one_json.items():
            final_json[key] = [value]
    df_row = pd.DataFrame(final_json)
    df_all_rows = pd.concat([df_all_rows,df_row])

df_all_rows.reset_index(inplace=True,drop=True)
# Final dataframe containing all the information related to a job posting extracted from the original webpage
df_final = pd.merge(df_jobs,df_all_rows,on=['Job Link'],how='outer')
df_final.fillna('',inplace=True)

# ------------------------------------------------- Styling the dataframe -------------------------------------------#
# Creating custom div tags with custom styling suitable to the user for better UI
div_1 = '<div style="width: 500px; height: 100px; overflow-y:scroll; vertical-align: top;">'
df_final['Job Summary'] = df_final['Job Summary'].apply(lambda val :  div_1 + val + '</div>')
df_final['Skills'] = df_final['Skills'].apply(lambda val :  div_1 + str(val) + '</div>')
df_final['Responsibilities'] = df_final['Responsibilities'].apply(lambda val :  div_1 + str(val) + '</div>')
df_final['Additional_Q'] = df_final['Additional_Q'].apply(lambda val :  div_1 + str(val) + '</div>')

div_2 = '<div style="width: 140px;height: 100px; vertical-align: top;">'
df_final['Date Posted'] = df_final['Date Posted'].apply(lambda val :  div_2 + str(val) + '</div>')
df_final['Job Title'] = df_final['Job Title'].apply(lambda val :  div_2 + str(val) + '</div>')
df_final['Comapny Name'] = df_final['Comapny Name'].apply(lambda val :  div_2 + str(val) + '</div>')

# custom_styling = [
#         {
#             "selector":"",
#             "props":[('border-left','0.5px solid black'),
#                  ('border-top','0.5px solid black'),
#                  ('border-bottom','0.5px solid black')
                     
#                 ]
#         },
        
#         {
#             "selector": "th",
#             "props": [
#                 ('width','100%'),
#                 ("background", "#00008B"),
#                 ("color", "white"),
#                 ("font-family", "tahoma"),
#                 ("text-align", "center"),
#                 ("font-size", "15px"),
#                 ("border-bottom",'0.5px solid black'),
#                 ("border-right",'0.5px solid black'),
#                 ('border-collapse','collapse')
#             ],
#         },
#         {
#             "selector": "td",
#             "props": [
#                 ("font-family", "tahoma"),
#                 ('text-align','top'),
#                 ("color", "black"),
#                 ("text-align", "left"),
#                 ("font-size", "15px"),
# #                 ('border-left','0.5px solid black'),
#                 ('border-right','0.5px solid black'),
#                 ('border-bottom','0.5px solid black'),
#                 ('border-collapse','collapse'),
#                 ('vertical-align','top')
                
#             ],
#         },

#         {"selector": "tr:hover", "props": [("background-color", "#d3d3d3")]}
#     ]

df_final_styled = (df_final.style
#                    .set_table_styles(custom_styling)
                   .format({"Job Link": make_clickable}))
# ---------------------------------------------- Dataframe styling ends --------------------------------------------------------#

# Loading the flask app and rendering the output
@app.route('/',methods=['GET','POST'])
def home():
    '''
    Flask view function to render the output on the UI displaying all the job postings extracted from various Job Portals
    '''
    print("Hello")
    # index_bs.html contains bootstrap classes that have been applied to the styled dataframe for better UI
    return render_template('index_bs.html',tables=[df_final_styled.hide_index().render()])
if '__main__' == __name__:
    app.run()