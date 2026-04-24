import json

path = r"C:\AI Project\Legal-chatbots\dataset\ner_finetune_data.jsonl"

with open(path, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

for i, item in enumerate(lines):
    item["id"] = i

with open(path, "w", encoding="utf-8") as f:
    for item in lines:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Done! Reindexed {len(lines)} records (0 -> {len(lines)-1})")
