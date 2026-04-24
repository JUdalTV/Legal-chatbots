import json
from collections import Counter

path = r"C:\AI Project\Legal-chatbots\dataset\ner_finetune_data.jsonl"

counter = Counter()
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            for label in json.loads(line)["labels"]:
                tag = label.split("-", 1)[1] if "-" in label else label
                counter[tag] += 1

print(f"Total unique entity types: {len(counter)}")
print(f"Total tokens: {sum(counter.values())}")
print()
print(f"{'Entity Type':<35} {'Count':>8}")
print("-" * 45)
for k, v in counter.most_common():
    print(f"{k:<35} {v:>8}")
