import requests
import time
from collections import Counter
import classla
import re

nlp = classla.Pipeline("sl", processors="tokenize,pos,lemma,ner", use_gpu=False)
classla.download("sl")

def ocisti_besedilo(besedilo):
    besedilo = re.sub(r"\s+", " ", besedilo)
    besedilo = re.sub(r"[^\w\s.,!?žščćčŠŽČĆ]", "", besedilo)
    return besedilo.strip()

def process_clanki(clanki_chunk):
    processed = []
    for i, clanek in enumerate(clanki_chunk):
        naslov = clanek.get("title", f"Članek {i}")
        besedilo = naslov + clanek.get("summary", "") + clanek.get("text", "")

        doc = nlp(ocisti_besedilo(besedilo))

        osebe = Counter()
        lokacije = Counter()
        organizacije = Counter()

        for ent in doc.ents:
            leme = []
            for sent in doc.sentences:
                for token in sent.tokens:
                    if token.start_char >= ent.start_char and token.end_char <= ent.end_char:
                        leme.append(token.words[0].lemma)
            besedilo_entitete = " ".join(leme) if leme else ent.text

            if ent.type == "PER":
                osebe[besedilo_entitete] += 1
            elif ent.type == "LOC":
                lokacije[besedilo_entitete] += 1
            elif ent.type == "ORG":
                organizacije[besedilo_entitete] += 1

        clanek["persons"] = dict(osebe)
        clanek["locations"] = dict(lokacije)
        clanek["organizations"] = dict(organizacije)
        processed.append(clanek)

    return processed

def main():
    while True:
        r = requests.get("http://10.0.0.2:5000/get_chunk")
        data = r.json()
        chunk_id = data["chunk_id"]
        if chunk_id is None:
            print("✅ Ni več dela, zaključi.")
            break
        startT=time.time()
        print(f"⬇️ Prevzemam chunk {chunk_id}")
        clanki = data["data"]
        rezultat = process_clanki(clanki)
        print(f"⬆️ Pošiljam rezultat za chunk {chunk_id}, porabljen cas: {time.time()-startT}")

        requests.post("http://10.0.0.2:5000/submit_result", json={
            "chunk_id": chunk_id,
            "result": rezultat
        })
        time.sleep(1)  # Malo pavze, da ne zadušiš strežnika

if __name__ == "__main__":
    main()import requests
import time
from collections import Counter
import classla
import re

nlp = classla.Pipeline("sl", processors="tokenize,pos,lemma,ner", use_gpu=False)
classla.download("sl")

def ocisti_besedilo(besedilo):
    besedilo = re.sub(r"\s+", " ", besedilo)
    besedilo = re.sub(r"[^\w\s.,!?žščćčŠŽČĆ]", "", besedilo)
    return besedilo.strip()

def process_clanki(clanki_chunk):
    processed = []
    for i, clanek in enumerate(clanki_chunk):
        naslov = clanek.get("title", f"Članek {i}")
        besedilo = naslov + clanek.get("summary", "") + clanek.get("text", "")

        doc = nlp(ocisti_besedilo(besedilo))

        osebe = Counter()
        lokacije = Counter()
        organizacije = Counter()

        for ent in doc.ents:
            leme = []
            for sent in doc.sentences:
                for token in sent.tokens:
                    if token.start_char >= ent.start_char and token.end_char <= ent.end_char:
                        leme.append(token.words[0].lemma)
            besedilo_entitete = " ".join(leme) if leme else ent.text

            if ent.type == "PER":
                osebe[besedilo_entitete] += 1
            elif ent.type == "LOC":
                lokacije[besedilo_entitete] += 1
            elif ent.type == "ORG":
                organizacije[besedilo_entitete] += 1

        clanek["persons"] = dict(osebe)
        clanek["locations"] = dict(lokacije)
        clanek["organizations"] = dict(organizacije)
        processed.append(clanek)

    return processed

def main():
    while True:
        r = requests.get("http://10.0.0.2:5000/get_chunk")
        data = r.json()
        chunk_id = data["chunk_id"]
        if chunk_id is None:
            print("✅ Ni več dela, zaključi.")
            break
        startT=time.time()
        print(f"⬇️ Prevzemam chunk {chunk_id}")
        clanki = data["data"]
        rezultat = process_clanki(clanki)
        print(f"⬆️ Pošiljam rezultat za chunk {chunk_id}, porabljen cas: {time.time()-startT}")

        requests.post("http://10.0.0.2:5000/submit_result", json={
            "chunk_id": chunk_id,
            "result": rezultat
        })
        time.sleep(1)  # Malo pavze, da ne zadušiš strežnika

if __name__ == "__main__":
    main()