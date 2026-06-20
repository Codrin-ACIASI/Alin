#!/usr/bin/env python3

import sys

current_word = None
current_doc_ids = []
word = None

for line in sys.stdin:
    line = line.strip()

    try:
        word, doc_id = line.split("\t", 1)
    except ValueError:
        continue

    if current_word == word:
        if doc_id not in current_doc_ids:
            current_doc_ids.append(doc_id)
    else:
        if current_word:
            print(f"{current_word}\t{current_doc_ids}")
        current_word = word
        current_doc_ids = [doc_id]

if current_word == word and current_word:
    print(f"{current_word}\t{current_doc_ids}")
