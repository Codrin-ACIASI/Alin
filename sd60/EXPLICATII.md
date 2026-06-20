# EXPLICATII.md — Ghid de Înțelegere a Soluției SPLSD-60

## Ce este un Indexed Inverted Index?

Un **Indexed Inverted Index** este structura de date fundamentală din spatele oricărui motor de căutare (Google, Elasticsearch etc.).

În loc să stochezi "ce cuvinte conține documentul X", stochezi invers: **"în ce documente apare cuvântul W"**.

### Exemplu

Dacă ai 3 documente:
- `doc1.txt`: "the fox is fast"
- `doc2.txt`: "the dog is slow"
- `doc3.txt`: "a fox and a dog"

Inverted Index-ul va arăta așa:

| Cuvânt | Documente |
|--------|-----------|
| the    | [doc1, doc2] |
| fox    | [doc1, doc3] |
| is     | [doc1, doc2] |
| fast   | [doc1] |
| dog    | [doc2, doc3] |
| slow   | [doc2] |
| a      | [doc3] |
| and    | [doc3] |

Acum dacă cineva caută "fox", știi instant că e în `doc1.txt` și `doc3.txt`.

---

## Arhitectura soluției — paradigma MapReduce

MapReduce împarte problema în 3 faze:

```
INPUT FILES → [MAP] → perechi intermediare → [SORT/SHUFFLE] → [REDUCE] → OUTPUT
```

### Faza 1: MAP

**Fișier**: `mapper_inverted_index.py`

Mapper-ul primește pe `stdin` liniile unui document și știe **numele documentului** din variabila de mediu `map_input_file` (setată de Hadoop automat, sau manual în rularea locală).

**Ce face fiecare linie de mapper:**

1. Citește o linie din document
2. O împarte în cuvinte (`split()`)
3. Curăță fiecare cuvânt: elimină punctuația, convertește la litere mici
4. Filtrează cuvintele care nu sunt exclusiv litere (`isalpha()`)
5. Emite perechea `(cuvânt, document_id)` pe `stdout`

**Exemplu concret:**
```
Input: "the quick brown fox"  (din doc1.txt)

Output:
the     doc1.txt
quick   doc1.txt
brown   doc1.txt
fox     doc1.txt
```

### Faza intermediară: SORT/SHUFFLE

Hadoop (sau comanda `sort` în varianta prin pipe) **sortează alfabetic** toate perechile emise de toți mapper-ii. Aceasta este cheia întregii paradigme MapReduce:

```
Toate perechile sortate:
a       doc2.txt
animal  doc2.txt
dog     doc1.txt
dog     doc3.txt
fox     doc1.txt
fox     doc2.txt
fox     doc3.txt
the     doc1.txt
the     doc2.txt
...
```

Sortarea garantează că **toate aparițiile aceluiași cuvânt vin consecutive** — reducer-ul poate astfel agrega fără să aibă nevoie de memorie globală.

### Faza 2: REDUCE

**Fișier**: `reducer_inverted_index.py`

Reducer-ul primește pe `stdin` perechile sortate și:

1. Menține o variabilă `current_word` și o listă `current_doc_ids`
2. Când cuvântul **se schimbă**: afișează cuvântul precedent cu lista de documente, resetează
3. **Deduplicare**: verifică `if doc_id not in current_doc_ids` pentru a nu repeta același document (un cuvânt poate apărea de mai multe ori în același document)
4. La finalul fișierului: afișează ultimul cuvânt (altfel s-ar pierde)

**De ce funcționează fără memorie globală?** Exact pentru că sortarea din faza anterioară garantează că toate rândurile pentru "fox" vin consecutive — reducer-ul nu trebuie să "caute" în tot fișierul, doar urmărește când se schimbă cheia.

---

## Fișierele soluției

### `mapper_inverted_index.py`

```python
document_id = os.environ.get("map_input_file", "unknown_doc")
document_id = os.path.basename(document_id)
```

`os.path.basename()` extrage doar numele fișierului din path-ul complet (`/home/hduser/input/doc1.txt` → `doc1.txt`). Astfel output-ul este mai clar și portabil.

```python
clean_word = word.strip(string.punctuation + "—''""")
clean_word = clean_word.lower()
if len(clean_word) > 0 and clean_word.isalpha():
```

Curățarea asigură că "fox," și "fox" sunt tratate ca același cuvânt. `isalpha()` elimină numere, simboluri speciale etc.

### `reducer_inverted_index.py`

```python
if doc_id not in current_doc_ids:
    current_doc_ids.append(doc_id)
```

Aceasta este deduplicarea in-place. Dacă cuvântul "the" apare de 5 ori în `doc1.txt`, documentul va fi adăugat o singură dată în lista finală.

### `run_local.py`

Simulează întregul pipeline MapReduce **fără Hadoop**, în Python pur. Util pentru:
- Testare rapidă pe orice mașină
- Debugging (poți adăuga print-uri)
- Demonstrație fără setup Hadoop

Logica internă urmează exact același flux: apelează `mapper()` pentru fiecare fișier, colectează toate perechile, le sortează, apoi apelează `reducer()`.

---

## De ce această arhitectură?

### Alternativa naivă (fără MapReduce)

```python
index = {}
for doc in documents:
    for word in doc:
        index[word].append(doc_id)
```

Aceasta funcționează pe un singur calculator, dar **nu scalează**: dacă ai 10TB de documente, nu ai suficientă RAM și nu poți paraleliza.

### Avantajul MapReduce

- **Paralelism**: mapper-ii rulează simultan pe noduri diferite, fiecare procesând o bucată din date
- **Fault tolerance**: dacă un nod pică, Hadoop redistribuie task-ul
- **Scalabilitate**: adaugi noduri și crești throughput-ul liniar
- **Decuplare**: mapper-ul nu știe de reducer și viceversa — comunicarea e prin stdout/stdin

### De ce `sort` între map și reduce?

Sortarea este ceea ce face ca reducer-ul să fie simplu și eficient. Fără ea, ar trebui un dicționar global care să acumuleze toate aparițiile unui cuvânt — imposibil de distribuit. Cu ea, reducerea e un simplu "parcurge și grupează grupuri consecutive identice".

---

## Fluxul complet vizual

```
doc1.txt ─┐
           ├─► [mapper] ─► (fox, doc1), (dog, doc1), (the, doc1) ...
doc2.txt ─┤                                                        │
           ├─► [mapper] ─► (fox, doc2), (the, doc2), (a, doc2)... │
doc3.txt ─┘                                                        │
                                                                   │
                          ┌────────────────────────────────────────┘
                          ▼
                    [SORT/SHUFFLE]
                    (a, doc2)
                    (dog, doc1)
                    (dog, doc3)
                    (fox, doc1)
                    (fox, doc2)
                    (fox, doc3)
                    (the, doc1)
                    (the, doc2)
                          │
                          ▼
                      [reducer]
                    a    → [doc2]
                    dog  → [doc1, doc3]
                    fox  → [doc1, doc2, doc3]
                    the  → [doc1, doc2]
                          │
                          ▼
                    output_local.txt / part-00000
```

---

## Întrebări frecvente

**Q: De ce `map_input_file` și nu un argument CLI?**  
A: Hadoop Streaming setează această variabilă de mediu automat pentru fiecare task de map. E standardul pentru a ști ce fișier procesezi.

**Q: De ce deduplicăm în reducer și nu în mapper?**  
A: Am putea deduplica și în mapper (emit o singură dată per (cuvânt, doc)), dar reducer-ul este locul natural pentru agregare în MapReduce. Alternativ, un combiner ar putea face pre-agregare locală.

**Q: Ce se întâmplă dacă același cuvânt apare de 1000 de ori în doc1.txt?**  
A: Mapper-ul va emite 1000 de perechi `(cuvânt, doc1.txt)`. Reducer-ul le va procesa pe toate, dar datorită verificării `if doc_id not in current_doc_ids`, `doc1.txt` va apărea o singură dată în output. În Hadoop real, un **Combiner** (egal cu reducer-ul în acest caz) ar putea deduplica local înainte de shuffle, reducând traficul de rețea.

**Q: De ce `clean_word.isalpha()` și nu `re.match(r'[a-z]+', clean_word)`?**  
A: `isalpha()` suportă și caractere non-ASCII (ă, â, î etc.), util pentru texte în română sau alte limbi. Regex-ul `[a-z]+` ar exclude cuvinte românești.
