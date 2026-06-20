#!/usr/bin/env python3

import sys
import os
import string

document_id = os.environ.get("map_input_file", "unknown_doc")
document_id = os.path.basename(document_id)

for line in sys.stdin:
    line = line.strip()
    words = line.split()
    for word in words:
        clean_word = word.strip(string.punctuation + "\u2014\u2018\u2019\u201c\u201d")
        clean_word = clean_word.lower()
        if len(clean_word) > 0 and clean_word.isalpha():
            print(f"{clean_word}\t{document_id}")
