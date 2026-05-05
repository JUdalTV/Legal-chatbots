import json
from collections import Counter

files = {
    "TRAIN": r"C:\AI Project\Legal-chatbots\dataset\ner_finetune_data.jsonl",
    "VAL":   r"C:\AI Project\Legal-chatbots\dataset\ner_val.jsonl",
    "TEST":  r"C:\AI Project\Legal-chatbots\dataset\ner_test.jsonl",
}

all_entities = {}
all_counts = {}

for name, path in files.items():
    with open(path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    ids = [item["id"] for item in lines]
    sequential = all(ids[i] == i for i in range(len(ids)))
    dupes = len(ids) - len(set(ids))

    # Check tokens == labels length
    mismatch = []
    empty_labels = []
    empty_tokens = []
    for item in lines:
        if len(item["tokens"]) != len(item["labels"]):
            mismatch.append(item["id"])
        if not item["labels"]:
            empty_labels.append(item["id"])
        if not item["tokens"]:
            empty_tokens.append(item["id"])

    # Check BIO consistency
    bio_errors = []
    for item in lines:
        prev = "O"
        for i, label in enumerate(item["labels"]):
            if label.startswith("I-"):
                entity = label[2:]
                if prev != f"B-{entity}" and prev != f"I-{entity}":
                    bio_errors.append((item["id"], i, label, prev))
                    break
            prev = label

    # Count entities
    counter = Counter()
    for item in lines:
        for label in item["labels"]:
            tag = label.split("-", 1)[1] if "-" in label else label
            counter[tag] += 1

    all_entities[name] = set(counter.keys())
    all_counts[name] = counter

    print(f"{'=' * 60}")
    print(f" {name}: {path.split(chr(92))[-1]}")
    print(f"{'=' * 60}")
    print(f" Records:           {len(lines)}")
    print(f" ID sequential:     {'OK' if sequential else 'FAIL'}")
    print(f" Duplicate IDs:     {dupes}")
    print(f" Token/Label match: {'OK' if not mismatch else f'FAIL at ids {mismatch[:5]}'}")
    print(f" Empty tokens:      {len(empty_tokens)}")
    print(f" Empty labels:      {len(empty_labels)}")
    print(f" BIO errors:        {len(bio_errors)}")
    if bio_errors:
        for bid, idx, lbl, prev in bio_errors[:3]:
            print(f"   id={bid}, pos={idx}, label={lbl}, prev={prev}")
    print(f" Entity types:      {len(counter)}")
    print(f" Total tokens:      {sum(counter.values())}")
    print()

# Compare
print(f"{'=' * 60}")
print(" ENTITY COVERAGE")
print(f"{'=' * 60}")
t, v, te = all_entities["TRAIN"], all_entities["VAL"], all_entities["TEST"]
print(f" Train: {len(t)}  |  Val: {len(v)}  |  Test: {len(te)}")
if t - v:  print(f" Train but NOT Val:  {sorted(t - v)}")
if t - te: print(f" Train but NOT Test: {sorted(t - te)}")
if v - t:  print(f" Val but NOT Train:  {sorted(v - t)}")
if te - t: print(f" Test but NOT Train: {sorted(te - t)}")
if not (t-v) and not (t-te) and not (v-t) and not (te-t):
    print(" All entities consistent across splits!")

# Ratio
total = sum(len(open(p, encoding="utf-8").readlines()) for p in files.values())
print(f"\n Split ratio:")
for name, path in files.items():
    with open(path, "r", encoding="utf-8") as f:
        n = sum(1 for l in f if l.strip())
    print(f"  {name}: {n} ({n/total*100:.1f}%)")
