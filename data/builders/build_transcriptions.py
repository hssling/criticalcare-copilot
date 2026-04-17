import pandas as pd
import json

df = pd.read_csv('data/raw/mtsamples.csv')
df = df.dropna(subset=['transcription', 'medical_specialty'])

records = []
for idx, row in df.iterrows():
    text = row['transcription']
    spec = row['medical_specialty']
    
    # We map this to our extraction schema
    record = {
        "task": "icu_summary", # Base task
        "case": {
            "patient_id": f"MTS-{idx}",
            "history": [spec.strip()],
            "vitals": {},
            "labs": {},
            "text_notes": text
        },
        "target": {
            "summary": f"Patient consultation for {spec.strip()}",
            "alerts": [],
            "missing_data": [],
            "recommendations": []
        }
    }
    records.append(record)

with open('data/processed/train.jsonl', 'w', encoding='utf-8') as f:
    for r in records:
        f.write(json.dumps(r) + '\n')
        
with open('data/processed/valid.jsonl', 'w', encoding='utf-8') as f:
    for r in records[:50]: # mock valid set
        f.write(json.dumps(r) + '\n')

print(f"Built {len(records)} training cases")
