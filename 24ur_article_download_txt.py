import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import json
import os
from datetime import datetime

def dodaj_artikel(link):
    # Ime datoteke
    datoteka = "obdelani_artikli.json"

    # Preveri, če datoteka obstaja; če ne, inicializiraj prazen seznam
    if os.path.exists(datoteka):
        with open(datoteka, "r", encoding="utf-8") as f:
            try:
                podatki = json.load(f)
            except json.JSONDecodeError:
                podatki = []
    else:
        podatki = []

    # Dodaj nov artikel s trenutnim časom
    nov_artikel = {
        "link": link,
        "date": datetime.now().isoformat()
    }
    podatki.append(nov_artikel)

    # Zapiši nazaj v datoteko
    with open(datoteka, "w", encoding="utf-8") as f:
        json.dump(podatki, f, ensure_ascii=False, indent=4)

    print(f"Artikel z linkom '{link}' je bil dodan.")


def download_article(url):
    # Prenesi HTML dokument s spleta
    response = requests.get(url)
    response.raise_for_status()  # Preveri, ali je bil prenos uspešen

    # Pridobi ime datoteke iz URL-ja
    file_name = "clanki/html/"+url.split("/")[-1].split("?")[0]
    if not file_name.endswith(".html"):
        file_name += ".html"

    # Shrani preneseni HTML dokument
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(response.text)

    return file_name

def extract_article(file_name, url):
    # Odpri in preberi HTML datoteko
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    # Ustvari BeautifulSoup objekt
    soup = BeautifulSoup(content, "html.parser")

    # Poišči element <article>
    article = soup.find("article")

    if article:
        # Poišči naslov članka <h1>
        title = article.find("h1").get_text().strip() if article.find("h1") else "Brez naslova"

        # Odstrani neželeno besedilo: datum, čas branja, lokacijo
        unwanted_elements = article.find_all("div", class_="text-black/60")
        for elem in unwanted_elements:
            elem.decompose()  # Odstrani element iz DOM-a

        # Ročno odstrani vrstico z datumom in lokacijo, če obstaja
        for p in article.find_all("p"):
            if re.match(r"^\w+, \d{2}\. \d{2}\. \d{4} \d{2}\.\d{2} \|.*", p.get_text().strip()):
                p.decompose()  # Odstrani odstavek
            elif "PRAVILA ZA OBJAVO KOMENTARJEV" in p.get_text().strip():
                p.decompose()  # Odstrani odstavek s pravili za objavo komentarjev
        # Poišči vse odstavke znotraj <article> in filtriraj po dolžini
        paragraphs = article.find_all("p")
        filtered_paragraphs = [p.get_text().strip() for p in paragraphs if len(p.get_text().split()) >= 10]

        # Pripravi ime izhodne datoteke (.txt)
        output_file_name = os.path.splitext(file_name)[0] + ".txt"

        # Zapiši naslov in filtrirane odstavke v datoteko
        with open(output_file_name, "w", encoding="utf-8") as output_file:
            output_file.write(title + "\n\n")  # Zapiši naslov
            for paragraph in filtered_paragraphs:
                output_file.write(paragraph + "\n\n")
        dodaj_artikel(url)
        print(f"Članek je bil uspešno shranjen v {output_file_name}.")
    else:
        print("Element <article> ni bil najden.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uporaba: python script.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    file_name = download_article(url)
    extract_article(file_name, url)

