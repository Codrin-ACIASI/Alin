#!/usr/bin/env python3

import os
import sys
import string
from collections import defaultdict

INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "input")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "output_local.txt")

def mapper(document_id, lines):
    pairs = []
    for line in lines:
        line = line.strip()
        words = line.split()
        for word in words:
            clean_word = word.strip(string.punctuation + "\u2014\u2018\u2019\u201c\u201d")
            clean_word = clean_word.lower()
            if len(clean_word) > 0 and clean_word.isalpha():
                pairs.append((clean_word, document_id))
    return pairs

def reducer(sorted_pairs):
    result = {}
    current_word = None
    current_docs = []

    for word, doc_id in sorted_pairs:
        if current_word == word:
            if doc_id not in current_docs:
                current_docs.append(doc_id)
        else:
            if current_word is not None:
                result[current_word] = list(current_docs)
            current_word = word
            current_docs = [doc_id]

    if current_word is not None:
        result[current_word] = list(current_docs)

    return result

def run():
    if not os.path.isdir(INPUT_DIR):
        print(f"[EROARE] Directorul de input nu exista: {INPUT_DIR}")
        sys.exit(1)

    all_pairs = []

    for filename in sorted(os.listdir(INPUT_DIR)):
        filepath = os.path.join(INPUT_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        document_id = filename
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        pairs = mapper(document_id, lines)
        all_pairs.extend(pairs)

    all_pairs.sort(key=lambda x: x[0])

    inverted_index = reducer(all_pairs)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for word, docs in sorted(inverted_index.items()):
            out.write(f"{word}\t{docs}\n")

    print(f"[OK] Indexed Inverted Index generat cu succes!")
    print(f"[OK] Output: {os.path.abspath(OUTPUT_FILE)}")
    print()
    print("=== REZULTAT (primele 20 intrari) ===")
    for i, (word, docs) in enumerate(sorted(inverted_index.items())):
        if i >= 20:
            print("... (vezi output_local.txt pentru rezultat complet)")
            break
        print(f"  {word:20s} -> {docs}")

if __name__ == "__main__":
    run()
