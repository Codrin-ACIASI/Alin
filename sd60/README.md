# SPLSD-60 — Indexed Inverted Index cu MapReduce

## Descriere

Implementare a paradigmei **MapReduce** pentru calculul unui **Indexed Inverted Index** pe un set de documente text.

- **Mapper**: parsează fiecare document și emite perechi `(cuvânt, document_id)`
- **Reducer**: grupează perechile și emite `(cuvânt, [document_id_1, document_id_2, ...])`

---

## Cerințe de sistem

- Python 3.6+
- (Opțional) Apache Hadoop 3.x cu Java 8 pentru rulare distribuită

---

## Structura proiectului

```
sd60/
├── src/
│   ├── mapper_inverted_index.py
│   ├── reducer_inverted_index.py
│   └── run_local.py
├── input/
│   ├── doc1.txt
│   ├── doc2.txt
│   └── doc3.txt
├── docs/
├── README.md
├── EXPLICATII.md
└── run.sh
```

---

## Rulare locală (fără Hadoop)

### 1. Clonare / extragere arhivă

```bash
cd sd60
```

### 2. Pregătire fișiere de input

Pune fișierele text în directorul `input/`. Fiecare fișier reprezintă un document separat.

### 3. Rulare script local

```bash
python3 src/run_local.py
```

Rezultatul va apărea în `output_local.txt` și în consolă.

### 4. Rulare prin pipe (simulare Hadoop Streaming)

```bash
for f in input/*.txt; do
    export map_input_file="$f"
    cat "$f" | python3 src/mapper_inverted_index.py
done | sort | python3 src/reducer_inverted_index.py
```

---

## Rulare cu Hadoop

### Cerințe

```bash
java -version   # trebuie să fie 1.8.x
hadoop version  # verificare Hadoop
```

### Pași

```bash
# 1. Pornire cluster
start-all.sh

# 2. Creare director input în HDFS
hdfs dfs -mkdir -p /user/hduser/input_sd60

# 3. Copiere fișiere de input în HDFS
hdfs dfs -put input/* /user/hduser/input_sd60/

# 4. Rulare job MapReduce
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming*.jar \
    -input /user/hduser/input_sd60 \
    -output /user/hduser/output_sd60 \
    -mapper "python3 mapper_inverted_index.py" \
    -reducer "python3 reducer_inverted_index.py" \
    -file src/mapper_inverted_index.py \
    -file src/reducer_inverted_index.py

# 5. Vizualizare rezultate
hdfs dfs -cat /user/hduser/output_sd60/part-00000

# 6. Copiere rezultate local
hdfs dfs -get /user/hduser/output_sd60/part-00000 output_hadoop.txt

# 7. Ștergere output pentru rulare repetată
hdfs dfs -rm -r /user/hduser/output_sd60
```

---

## Rulare automată

```bash
chmod +x run.sh
./run.sh
```

---

## Troubleshooting

### Python nu este instalat

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3

# Verificare
python3 --version
```

### Eroare: "No such file or directory: input/"

Asigură-te că directorul `input/` există și conține cel puțin un fișier `.txt`.

```bash
ls input/
```

### Hadoop: "Java version not supported"

Hadoop 3.x necesită **Java 8** (nu Java 11, nu Java 17).

```bash
sudo update-alternatives --config java
# Selectează intrarea cu jdk1.8.x
```

### Hadoop: "put: File could only be written to 0 of the 1 minReplication nodes"

DataNode-ul nu este activ. Resetează HDFS:

```bash
stop-all.sh
rm -rf /tmp/hadoop-*
hdfs namenode -format
start-all.sh
```

### Hadoop: "ipc.Client: Retrying connect to server: 0.0.0.0:8032"

Resource Manager-ul nu rulează:

```bash
start-yarn.sh
```

### Eroare permisiuni pe fișierele Python în Hadoop

```bash
chmod +x src/mapper_inverted_index.py
chmod +x src/reducer_inverted_index.py
```

### Rezultat gol

Verifică că fișierele din `input/` conțin text ASCII/UTF-8 valid și nu sunt binare.
