import json

files = [
    r"C:\AI Project\Legal-chatbots\dataset\ner_finetune_data.jsonl",
    r"C:\AI Project\Legal-chatbots\dataset\ner_val.jsonl",
    r"C:\AI Project\Legal-chatbots\dataset\ner_test.jsonl",
]

for path in files:
    with open(path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    bio_fixed = 0
    for idx, item in enumerate(lines):
        # Reindex
        item["id"] = idx

        # Fix BIO: I-X after different entity -> B-X
        labels = item["labels"]
        for i in range(len(labels)):
            if labels[i].startswith("I-"):
                entity = labels[i][2:]
                prev = labels[i - 1] if i > 0 else "O"
                if prev != f"B-{entity}" and prev != f"I-{entity}":
                    labels[i] = f"B-{entity}"
                    bio_fixed += 1

    with open(path, "w", encoding="utf-8") as f:
        for item in lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    name = path.split("\\")[-1]
    print(f"{name}: {len(lines)} records reindexed, {bio_fixed} BIO errors fixed")

print("\nDone!")
