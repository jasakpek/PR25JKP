from flask import Flask, request, jsonify
import json
import os
import time
import threading

app = Flask(__name__)

CHUNK_SIZE = 50
TIMEOUT_MINUTES = 15
CHUNKS_DIR = "vsi_chunki"
RESULTS_DIR = "obdelani_chunki"

os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True) 

# Nalaganje vseh člankov in razbitje na chunke
with open('combined.json', 'r', encoding='utf-8') as f:
    all_articles = json.load(f)

chunks = [
    all_articles[i:i + CHUNK_SIZE]
    for i in range(0, len(all_articles), CHUNK_SIZE)
]

# Shranimo vse vhodne chunke na disk
for i, chunk in enumerate(chunks):
    path = os.path.join(CHUNKS_DIR, f"chunk{i}.json")
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

# Naložimo že obdelane chunke
processed_ids = {
    int(filename.replace("chunk", "").replace(".json", ""))
    for filename in os.listdir(RESULTS_DIR)
    if filename.endswith(".json")
}

# V RAM-u sledimo trenutno dodeljenim chunkom
assigned = {}  # chunk_id (str) -> timestamp

lock = threading.Lock()

@app.route('/get_chunk', methods=['GET'])
def get_chunk():
    now = time.time()
    with lock:
        for i in range(len(chunks)):
            if i in processed_ids:
                continue

            assigned_time = assigned.get(str(i))
            if assigned_time is None or now - assigned_time > TIMEOUT_MINUTES * 60:
                assigned[str(i)] = now
                path = os.path.join(CHUNKS_DIR, f"chunk{i}.json")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({'chunk_id': i, 'data': data})

    return jsonify({'chunk_id': None, 'data': []})

@app.route('/submit_result', methods=['POST'])
def submit_result():
    data = request.get_json()
    chunk_id = data['chunk_id']
    result = data['result']

    with lock:
        # Shrani rezultat
        out_path = os.path.join(RESULTS_DIR, f"chunk{chunk_id}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        processed_ids.add(chunk_id)
        assigned.pop(str(chunk_id), None)

        print(f"✔️ Shranjen rezultat za chunk {chunk_id} ({len(processed_ids)}/{len(chunks)})")

        if len(processed_ids) == len(chunks):
            print("✅ Vsi chunki obdelani, sestavljam...")
            combined = []
            for i in range(len(chunks)):
                result_path = os.path.join(RESULTS_DIR, f"chunk{i}.json")
                with open(result_path, 'r', encoding='utf-8') as f:
                    combined.extend(json.load(f))
            with open('combined_processed.json', 'w', encoding='utf-8') as f:
                json.dump(combined, f, ensure_ascii=False, indent=2)

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)