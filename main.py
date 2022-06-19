# Source: https://www.youtube.com/watch?v=PPcgtx0sI2E

from bs4 import BeautifulSoup
import requests

def extract(page):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    url = f'https://uk.indeed.com/jobs?q=python+developer&l=London%2C+Greater+London&start={page}'
    r = requests.get(url, headers)
    soup = BeautifulSoup(r.content,'html.parser')
    return soup

def transform(soup):
    divs = soup.find_all('div',class_='job_seen_beacon')
    return divs[0]


c = extract(0)
print(transform(c))