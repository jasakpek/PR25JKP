#SKRIPTA JE KLON RAZDELI PO KATEGORIJA, KER JUPYTER POCEPNE.

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import os
import json
import time
import re

model_name = "cjvt/sloberta-trendi-topics"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def klasificiraj_teme(besedilo):
    inputs = tokenizer(besedilo, return_tensors="pt", truncation=True, max_length=512).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=1).squeeze().cpu().tolist()

    labels = model.config.id2label
    return {labels[i]: round(prob, 3) for i, prob in enumerate(probs)}

def izpisi_clanke():
    for i, clanek in enumerate(clanki, 1):
        print(clanek)

def save_clanki(filename="clanki_kategorized.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(clanki, f, ensure_ascii=False, indent=2)

def ocisti_besedilo(besedilo):
    besedilo = re.sub(r"\s+", " ", besedilo)  # Odvečne beline
    besedilo = re.sub(r"[^\w\s.,!?žščćčŠŽČĆ]", "", besedilo)  # Neobičajni znaki
    return besedilo.strip()

print(f"Nalagam datoteko: combined.json")
start= time.time()
with open('combined.json', 'r', encoding='utf-8') as f:
    clanki = json.load(f)
stop = time.time()
print(f"Za nalaganje datoteke smo porabili {stop-start:.0f} sekund")

print(f"Zacenjam kategorizacijo")
start = time.time()
for i, clanek in enumerate(clanki, 1):
    if(i%100==0):
        print(f"{i}/{len(clanki)}   {i*100/len(clanki):.4f}% Trenutno porabljen cas: {time.time()-start:.0f} sekund")
    title = clanek.get("title", "")
    summary = clanek.get("summary", "")
    text = clanek.get("text","")
    clanek["label_title"] = klasificiraj_teme(ocisti_besedilo(title))
    clanek["label_summary"] = klasificiraj_teme(ocisti_besedilo(summary))
    clanek["label_text"] = klasificiraj_teme(ocisti_besedilo(text))
    clanek["label"] = klasificiraj_teme(ocisti_besedilo(title + summary + text))
stop = time.time()
print(f"Za kategorizacijo {len(clanki)} clankov smo porabili: {stop-start:.0f} sekund")

save_clanki(filename="clanki_kategorizirani_po_vsem.json")