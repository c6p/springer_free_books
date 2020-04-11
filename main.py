import os
import pandas as pd
from tqdm import tqdm
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0' }

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get(url, **kwargs):
    try:
        return requests_retry_session().get(url, timeout=5, **kwargs)
    except:
        return


# insert here the folder you want the books to be downloaded:
folder = os.path.join(os.getcwd(), 'download')

if not os.path.exists(folder):
    os.mkdir(folder)

books = None
table_path = os.path.join(folder, 'table.xlsx')
if os.path.exists(table_path):
    books = pd.read_excel(table_path)
else:
    books = pd.read_excel('https://resource-cms.springernature.com/springer-cms/rest/v1/content/17858272/data/v4')
    books.to_excel(table_path)

downloaded = []
list_path = os.path.join(folder, 'list.txt')
try:
    with open(list_path, 'r') as f:
        downloaded = f.read().split('\n')
except:
    pass
f = open(list_path, 'a+')

missing = {}

print('Download started.')

pbar = tqdm(books[['OpenURL', 'Book Title', 'Author', 'English Package Name']].values)
for url, title, author, pk_name in pbar:
    pbar.set_description("Checking… %s" % title)
    if url in downloaded:
        continue

    new_folder = os.path.join(folder, pk_name)

    if not os.path.exists(new_folder):
        os.mkdir(new_folder)

    r = get(url)
    if not r:
        continue

    pdf, epub = False, False

    new_url = r.url
    new_url = new_url.replace('/book/','/content/pdf/')
    new_url = new_url.replace('%2F','/')
    new_url = new_url + '.pdf'

    final = new_url.split('/')[-1]
    final = title.replace(',','-').replace('.','').replace('/',' ') + ' - ' + author.replace(',','-').replace('.','').replace('/',' ') + ' - ' + final
    output_file = os.path.join(new_folder, final)
    if not os.path.exists(output_file):
        pbar.set_description("Getting PDF… %s" % title)
        request = get(new_url, allow_redirects=True)
        if request is not None and request.status_code in [200, 404]:
            pdf = True
            if request.status_code == 200:
                open(output_file, 'wb').write(request.content)
    else:
        pdf = True

    #download epub version too if exists
    new_url = r.url
    new_url = new_url.replace('/book/','/download/epub/')
    new_url = new_url.replace('%2F','/')
    new_url = new_url + '.epub'

    final = new_url.split('/')[-1]
    final = title.replace(',','-').replace('.','').replace('/',' ') + ' - ' + author.replace(',','-').replace('.','').replace('/',' ') + ' - ' + final
    output_file = os.path.join(new_folder, final)
    if not os.path.exists(output_file):
        pbar.set_description("Getting EPUB… %s" % title)
        request = get(new_url, allow_redirects=True)
        if request is not None and request.status_code in [200, 404]:
            epub = True
            if request.status_code == 200:
                open(output_file, 'wb').write(request.content)
    else:
        epub = True

    if pdf and epub:
        f.write(url+'\n')
    else:
        missing[title] = {'pdf':pdf, 'epub': epub}
    time.sleep(5)

f.close()
print('Download finished.')
if missing:
    print('\n! FILES MISSING:\n')
    for k,v in missing:
        print('{50:}'.format(k), '- epub -' if ['epub'] else '-      -', '- pdf -' if ['pdf'] else '-     -')
    print('\n! Execute again to get missing books')
