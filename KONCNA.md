# Poročilo: Analiza slovenskih novic iz spletnega mesta 24ur.com

## 1. Opis problema

Namen naloge je bila obsežna analiza novic iz slovenskega portala **24ur.com**, s poudarkom na:
- **ekstrakciji in normalizaciji entitet** (osebe, kraji, organizacije),
- **časovni analizi pojavnosti oseb** v novicah,
- **klasifikaciji člankov po tematikah** s pomočjo obstoječih slovenskih modelov.

Glavni cilji so bili:
- prenesti zgodovino člankov iz portala 24ur.com,
- prečistiti in strukturirati podatke v JSON formatu,
- analizirati vsebino člankov (osebe, organizacije, kraje),
- prikazati pogostost pojavljanja oseb skozi čas,
- pripraviti platformo za vizualizacijo rezultatov.

## 2. Pridobivanje in obdelava podatkov

### 2.1 Prenos in parsanje HTML vsebine

Prenesel sem **21 GB** HTML vsebine, kar ustreza približno **305.000 člankom**. Zaradi visoke količine neuporabnih podatkov v vsakem HTML-ju (95 %), sem s pomočjo Python skripte (`html_to_json.py`) izločil relevantne informacije:

- `title`: Naslov članka  
- `author`: Avtor članka (če obstaja)  
- `date`: Datum objave  
- `summary`: Povzetek članka  
- `text`: Glavno besedilo  
- `country`: Slovenija / tujina  
- `place`: Natančnejša lokacija (naselje, vas, mesto, država)

### 2.2 Popravljanje napak pri datumu

Zaradi napačne parsanja datuma pri ~700 člankih sem uporabil povratno logiko: iz naslova sem ponovno ustvaril ime izvorne HTML datoteke in iz nje ponovno prebral datum. To je delno uspelo pri **331 člankih**. Končno je ostalo le okoli **350 člankov z napačnim datumom**, kar predstavlja **zanemarljiv delež**.

### 2.3 Združevanje v enoten JSON dokument

Da bi zmanjšal počasno nesekvenčno branje iz diska, sem vse posamezne JSON datoteke združil v enoten seznam člankov, shranjenih v eno veliko datoteko.

---

## 3. Klasifikacija člankov po tematikah

Za tematsko razvrstitev člankov sem uporabil Huggingface model `cjvt/sloberta-trendi-topics`, ki dodeli verjetnosti za pripadnost vsakega članka eni izmed 13 kategorij.

Vsakemu članku sem dodal atribut `label_text`, ki vsebuje nabor ključev:

```json
"label_text": {
  "LABEL_0": 0.013,
  "LABEL_1": 0.563,
  ...
  "LABEL_12": 0.002
}
```

Trenutno rezultatov še nisem analiziral podrobneje, a podatki so pripravljeni za nadaljnjo uporabo.

## 4. Prepoznavanje entitet (oseb, krajev, organizacij)

### 4.1 Uporabljeni model in težave

Za ekstrakcijo entitet sem preizkusil več knjižnic in modelov, najboljše rezultate pa je dala **CLASSLA** z uporabo slovenskega modela. Pred obdelavo sem moral očistiti besedila, saj CLASSLA ob neurejenem vhodu vrača popolnoma napačne entitete.

### 4.2 Problem z zmogljivostmi

Ena CLASSLA instanca porabi več kot **8 GB RAM-a** in teče na največ 4 jedrih CPU-ja. Po prvotnih ocenah bi analiza vseh člankov trajala **približno 15 dni**.

### 4.3 Distribuirana rešitev

Zato sem implementiral razdeljen sistem:
- **`classla_server`**: Flask API strežnik, ki razdeljuje članke po `chunksize=50` klientom
- **`classla_worker`**: Odjemalci, ki obdelujejo dodeljene članke

Distribucija je tekla na 4 stalnih računalnikih in občasno na dodatnih domačih napravah. Ta sistem je omogočil razumno hitro obdelavo, po porabljenih nekaj kW elektrike in dveh napornih dneh so se računalniki le prebili dokonca :)

### 4.4 Normalizacija imen oseb

Ker so se imena oseb pojavljala v več različicah (npr. “Janez Janša” in “Janša”), sem naredil **slovar popravkov**, kjer so variacije mapirane na enotno ime. Slovar je bil ročno generiran (s pomočjo ChatGPT) za **2642 najpogosteje omenjenih oseb**. Ta pristop nam omogoča vkljop ali izkljop normalizacije.

## 5. Struktura končnega podatkovnega zapisa

Vsak članek je po obdelavi zapisan v JSON formatu z naslednjimi atributi:

```json
{
  "title": "...",
  "author": "...",
  "date": "...",
  "summary": "...",
  "text": "...",
  "country": "slovenija|tujina",
  "place": "...",
  "persons": {
    "Janez Janša": 2,
    "Pahor": 1
  },
  "locations": { ... },
  "organizations": { ... },
  "label_text": { "LABEL_0": 0.1, ..., "LABEL_12": 0.05 }
}
```
## 6. Analiza oseb

Na osnovi obdelanih podatkov sem pripravil **vizualizacijo oseb skozi čas**, kjer lahko uporabnik:

- izbere **časovno obdobje**,
- določi ali naj se šteje **vsaka omemba ali le ena na članek**,
- omogoči uporabo **normaliziranih imen** preko slovarja popravkov,
- nastavi prikaz **N najbolj pogostih oseb** v grafu.

Ta funkcionalnost je vključena v **Streamlit aplikacijo**, ki omogoča enostavno raziskovanje rezultatov, dostopna pa je na povazavi 1kp3.com:8501.

## 7. Zaključek

Projekt je zahteval veliko tehničnega znanja in potrpežljivosti. Največje izzive so predstavljali:
- **velikost in oblika podatkov** (305.000 člankov, 21GB),
- **učinkovita obdelava naravnega jezika** za slovenščino,
- **optimizacija obdelave z razdeljenim sistemom**,
- **normalizacija entitet**, ki je ključna za smiselno analizo.

Rezultat je **bogata baza strukturiranih slovenskih člankov**, pripravljena za nadaljnje raziskave in analize (npr. korelacija med osebami, analiza tematskih premikov ipd.).

## 8. Priloge

- `html_to_json.py` – skripta za pretvorbo HTML v JSON
- `classla_server.py`, `classla_worker.py` – za porazdeljeno obdelavo entitet
- `testNER.ipynb` – z analizo razlike med čiščenim in nečiščenim besedilom
- `pripravi_imenske_popravke.ipynb` – pomaga pri pripravi slovarja imenski_popravki.json
- `popravi_datume.ipynb` – python notebook s katerim sem popravil datume
- `Graf_osebe_skozi_cas.ipynb` – Primer analize pojavnosti oseb
- `Graf_organizacije_skozi_cas.ipynb` – Primer analize pojavnosti organizacij
- `Najpogostejsih_10_imen.ipynb` – Primerjava normaliziranih vs nenormaliziranih imen
- `imenski_popravki.json` – slovar normalizacije oseb
- `app.py` – aplikacija za analizo in prikaz rezultatov
```
