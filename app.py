import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict, Counter
import json
from pathlib import Path
import numpy as np

# ---------- Podatki: clanki in imenski popravki ----------

@st.cache_data
def load_articles():
    with open('../combined_finish.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_name_corrections(pot="../imenski_popravki.json"):
    if Path(pot).exists():
        with open(pot, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

CLANKI = load_articles()
IMENSKI_POPRAVKI = load_name_corrections()

def popravi_ime(ime):
    popravljeno = IMENSKI_POPRAVKI.get(ime, ime)
    return ime if popravljeno == '' else popravljeno

# ---------- Logika za izris grafa ----------

def izrisi_top_osebe(clanki,datum_od,datum_do,ponovitve=True,num=10,chatgpt_popravek=True,label=None,label_prag=0.0):
    datum_od = datetime.strptime(datum_od, "%d. %m. %Y")
    datum_do = datetime.strptime(datum_do, "%d. %m. %Y")

    stevci = defaultdict(int)

    for clanek in clanki:
        try:
            datum_clanka = datetime.strptime(clanek["date"].strip(), "%d. %m. %Y %H.%M")
        except:
            continue

        if not (datum_od <= datum_clanka <= datum_do):
            continue

        # --- FILTER LABEL ---
        if label and label != "(poljubno)":
            probability = clanek.get("label_text", {}).get(label, 0.0)
            if probability < label_prag:
                continue

        persons = clanek.get("persons", {})
        ze_dodani = set()

        for ime, count in persons.items():
            if chatgpt_popravek:
                pravo_ime = popravi_ime(ime)
            else:
                pravo_ime = ime
            if pravo_ime is None:
                continue
            if ponovitve:
                stevci[pravo_ime] += count
            else:
                if pravo_ime not in ze_dodani:
                    stevci[pravo_ime] += 1
                    ze_dodani.add(pravo_ime)

    najpogostejsi = Counter(stevci).most_common(num)
    imena = [ime for ime, _ in najpogostejsi]
    stevila = [stevilo for _, stevilo in najpogostejsi]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(imena[::-1], stevila[::-1], color='skyblue')
    ax.set_xlabel('Pojavitve' if ponovitve else 'Št. člankov z omembo')
    range_txt = f"Top {num} oseb med {datum_od.strftime('%d.%m.%Y')} in {datum_do.strftime('%d.%m.%Y')}"
    if label and label != "(poljubno)":
        range_txt += f"\n(samo članki z labelo {label}, p ≥ {label_prag})"
    ax.set_title(range_txt)
    plt.tight_layout()

    return fig

def drsece_povprecje(vrednosti, okno=3):
    """Glajenje vrednosti z drsečim povprečjem."""
    if len(vrednosti) < okno:
        return vrednosti  # Ni dovolj točk
    return np.convolve(vrednosti, np.ones(okno)/okno, mode='same')

def graphPrepoznavnosti(clanki, imena, datum_od, datum_do, popravek=True, poenostavi=False, okno=3):
    if isinstance(imena, str):
        imena = [imena]  # Pretvori v seznam, če podan niz

    datum_od = datetime.strptime(datum_od, "%d. %m. %Y")
    datum_do = datetime.strptime(datum_do, "%d. %m. %Y")

    vse_pojavitve = {ime: defaultdict(int) for ime in imena}

    for clanek in clanki:
        try:
            datum_clanka = datetime.strptime(clanek["date"].strip(), "%d. %m. %Y %H.%M")
        except (KeyError, ValueError):
            continue

        if not (datum_od <= datum_clanka <= datum_do):
            continue

        persons = clanek.get("persons", {})

        for izvirno_ime in imena:
            if popravek:
                for person_ime, stevilo in persons.items():
                    norm_ime = popravi_ime(person_ime)
                    if norm_ime == izvirno_ime:
                        vse_pojavitve[izvirno_ime][datum_clanka.date()] += stevilo
            else:
                if izvirno_ime in persons:
                    vse_pojavitve[izvirno_ime][datum_clanka.date()] += persons[izvirno_ime]

    if all(not vrednosti for vrednosti in vse_pojavitve.values()):
        print("Za nobeno osebo ni pojavitev v danem obdobju.")
        return

    plt.figure(figsize=(12, 6))

    for ime, pojavitve_po_dnevih in vse_pojavitve.items():
        if not pojavitve_po_dnevih:
            continue

        datumi = sorted(pojavitve_po_dnevih)
        pojavitve = [pojavitve_po_dnevih[datum] for datum in datumi]

        if poenostavi:
            pojavitve = drsece_povprecje(pojavitve, okno)

        plt.plot(datumi, pojavitve, linestyle='-', label=ime)

    plt.title(f"Pojavitve oseb od {datum_od.date()} do {datum_do.date()}")
    plt.xlabel("Datum")
    plt.ylabel("Število pojavitev")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    return plt.gcf()
# ---------- UI aplikacije ----------

def stran_analiza_oseb():
    st.title("Analiza pojavnosti oseb v člankih")

    st.markdown("### Izberi parametre za graf:")
    col1, col2 = st.columns(2)

    with col1:
        datum_od = st.text_input("Datum od (npr. 01. 01. 2020)", "01. 01. 1900")
    with col2:
        datum_do = st.text_input("Datum do (npr. 31. 12. 2023)", "31. 12. 2030")

    ponovitve = st.radio("Kaj šteješ kot pojavitev?", ["Vsako omembo", "Le enkrat na članek"])
    popravek = st.radio("Ali zelis uporabiti ChatGPT generiran seznam popravljenih imen:", ["Da", "Ne"])
    num = st.slider("Koliko oseb prikazati?", min_value=5, max_value=30, value=10)
    
    # Dodatek: izbira labela in verjetnosti
    labeli = [f"LABEL_{i}" for i in range(13)]
    izbrani_label = st.selectbox("Filtriraj članke po labelu (opcijsko):", ["(poljubno)"] + labeli)
    prag_verjetnost = st.slider("Minimalna verjetnost za label (če izberete label):", 0.0, 1.0, 0.5, 0.05)

    if st.button("Izriši graf"):
        try:
            # Če je "(poljubno)", parameter posreduj kot None
            label_param = None if izbrani_label == "(poljubno)" else izbrani_label
            fig = izrisi_top_osebe(
                clanki=CLANKI,
                datum_od=datum_od,
                datum_do=datum_do,
                ponovitve=(ponovitve == "Vsako omembo"),
                num=num,
                chatgpt_popravek=(popravek == "Da"),
                label=label_param,
                label_prag=prag_verjetnost
            )
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Napaka pri izrisu: {e}")

def stran_iskanje_clankov():
    st.title("Iskanje člankov")

    st.markdown("### Filtriraj po:")

    # Vnos datumov
    col1, col2 = st.columns(2)
    with col1:
        datum_od = st.text_input("Datum od (npr. 01. 01. 2020)", "01. 01. 1900")
    with col2:
        datum_do = st.text_input("Datum do (npr. 31. 12. 2023)", "31. 12. 2030")

    # Seznam labelov
    labeli = [f"LABEL_{i}" for i in range(13)]
    izbrani_label = st.selectbox("Izberi label:", ["(poljubno)"] + labeli)

    # Prag verjetnosti
    prag = st.slider("Minimalna verjetnost za label (če izbran):", 0.0, 1.0, 0.5, 0.05)

    if st.button("Poišči članke"):
        try:
            datum_od_dt = datetime.strptime(datum_od, "%d. %m. %Y")
            datum_do_dt = datetime.strptime(datum_do, "%d. %m. %Y")
        except ValueError:
            st.error("Datuma morata biti v formatu DD. MM. YYYY")
            return

        rezultati = []
        for clanek in CLANKI:
            # Preveri datum
            try:
                datum_clanka = datetime.strptime(clanek["date"].strip(), "%d. %m. %Y %H.%M")
            except:
                continue

            if not (datum_od_dt <= datum_clanka <= datum_do_dt):
                continue

            # Če je izbran label, preveri verjetnost
            if izbrani_label != "(poljubno)":
                verjetnosti = clanek.get("label_text", {})
                p = verjetnosti.get(izbrani_label, 0.0)
                if p < prag:
                    continue

            rezultati.append((datum_clanka, clanek))

        st.success(f"Najdenih {len(rezultati)} člankov.")
        for datum_clanka, clanek in sorted(rezultati, key=lambda x: x[0], reverse=True)[:100]:
            st.markdown(f"**{datum_clanka.strftime('%d. %m. %Y %H:%M')}**")
            st.markdown(f"- Naslov: `{clanek.get('title', 'Ni naslova')}`")
            
            verj_text = clanek.get("label_text", {})
            label_info = ", ".join([f"{k}: {v:.2f}" for k, v in verj_text.items()])
            st.markdown(f"- Verjetnosti labelov: `{label_info}`")
            
            osebe = clanek.get("persons", {})
            if osebe:
                osebe_sorted = sorted(osebe.items(), key=lambda x: -x[1])
                osebe_str = ", ".join([f"{ime} ({stevilo})" for ime, stevilo in osebe_sorted])
                st.markdown(f"**Osebe:** {osebe_str}")
            else:
                st.markdown("*Ni zaznanih oseb.*")
            st.markdown("---")

def stran_graf_prepoznavnosti():
    st.title("Graf prepoznavnosti oseb skozi čas")

    st.markdown("### Parametri za izris grafa:")

    imena_vnos = st.text_input("Vnesi ime ali več imen (ločena z vejico)", "Janez Janša, Robert Golob")
    imena = [ime.strip() for ime in imena_vnos.split(",") if ime.strip()]

    col1, col2 = st.columns(2)
    with col1:
        datum_od = st.text_input("Datum od (npr. 01. 01. 2020)", "01. 01. 2020")
    with col2:
        datum_do = st.text_input("Datum do (npr. 31. 12. 2023)", "31. 12. 2023")

    popravek = st.checkbox("Uporabi popravke imen (ChatGPT)", value=True)
    poenostavi = st.checkbox("Glajenje z drsečim povprečjem", value=True)
    okno = st.slider("Velikost okna za drseče povprečje", min_value=1, max_value=100, value=3)

    if st.button("Izriši graf prepoznavnosti"):
        try:
            fig = graphPrepoznavnosti(
                clanki=CLANKI,
                imena=imena,
                datum_od=datum_od,
                datum_do=datum_do,
                popravek=popravek,
                poenostavi=poenostavi,
                okno=okno
            )
            if fig:
                st.pyplot(fig)
            else:
                st.warning("Ni dovolj podatkov za izris grafa.")
        except Exception as e:
            st.error(f"Napaka: {e}")


            
def main():
    stran = st.sidebar.radio("Izberi stran", ["Analiza oseb", "Iskanje člankov", "Graf prepoznavnosti"])

    if stran == "Analiza oseb":
        stran_analiza_oseb()
    elif stran == "Iskanje člankov":
        stran_iskanje_clankov()
    elif stran == "Graf prepoznavnosti":
        stran_graf_prepoznavnosti()
        
if __name__ == "__main__":
    main()