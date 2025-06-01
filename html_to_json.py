import requests
from bs4 import BeautifulSoup
import time
import os
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR="./json/"
CORS=24



def naslov(soup):
    naslov = soup.find("h1").get_text(strip=True)
    if "|" in naslov:
        naslov = naslov.split("|")[0].strip()

    return naslov
def avtor(soup):
    for span in soup.find_all('span'):
        if span.get_text(strip=True) == "Avtor":
            return span.parent.find('div').get_text(strip=True)
    return ""
def drzava(soup):
    return soup.select_one('article > div > div > div').get_text(strip=True)
def kraj(soup):
    return soup.select_one('article > div > p').get_text(strip=True).split(",")[0]
def datum(soup):
    return soup.select_one('article > div > p').get_text(strip=True).split(",")[1].split("|")[0]
def povzetek(soup):
    return soup.find('p', class_='text-article-summary').get_text(strip=True)
def besedilo(soup):
    besedilo=""
    for p in soup.find('div', class_='article__body').find_all('p'):
        besedilo=besedilo+p.get_text()+"\n"
    return besedilo.replace('\xa0', ' ')    

def clanek_to_json(clanek_html, clanek_json):
    with open(clanek_html, 'r', encoding='utf-8') as f:
        article=BeautifulSoup(f, 'html.parser')
    result = {
        "title": naslov(article),
        "author": avtor(article),
        "country": drzava(article),
        "place": kraj(article),
        "date": datum(article),
        "summary": povzetek(article),
        "text": besedilo(article)
    }
    with open(clanek_json, 'w', encoding='utf-8') as f_out:
        json.dump(result, f_out, ensure_ascii=False, indent=2)

def process_files(array_html_datotek):
    for html_file in array_html_datotek:
        base_name = os.path.splitext(html_file)[0]
        json_file = JSON_DIR + html_file.rsplit('.', 1)[0].split('/')[-1] + '.json'
        clanek_to_json(html_file, json_file)
def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

html_dir = './html'
html_files = ["./html/"+f for f in os.listdir('./html') if f.endswith('.html')]
print("Primer: "+html_files[10])

print(f"Najdenih {len(html_files)} .html datotek.")

# 2. Razdelimo v chunke po 1000 datotek
chunk_size = 420
chunks = list(chunk_list(html_files, chunk_size))

print(f"Ustvarjenih {len(chunks)} chunkov.")
def run_parallel(chunks, max_workers=8):
    total = len(chunks)
    completed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_files, chunk) for chunk in chunks]

        for future in as_completed(futures):
            try:
                future.result()  # preveri napake
            except Exception as e:
                print(f"Napaka pri obdelavi: {e}")

            completed += 1
            print(f"Napredek: {completed}/{total} ({completed * 100 // total}%)")
run_parallel(chunks, max_workers=24)
        