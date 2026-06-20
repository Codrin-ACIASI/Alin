# Diagrama de clase — SPLSD-60 Inverted Index MapReduce

Diagrama de mai jos reprezintă arhitectura logică a soluției în format Mermaid.
Poate fi randată pe https://mermaid.live sau în orice editor Markdown cu suport Mermaid.

```mermaid
classDiagram
    class Mapper {
        -document_id : str
        +read_stdin() list~tuple~
        +clean_word(word: str) str
        +emit(word: str, doc_id: str) void
        +run() void
    }

    class Reducer {
        -current_word : str
        -current_doc_ids : list~str~
        +read_stdin() list~tuple~
        +deduplicate(doc_id: str) bool
        +emit(word: str, doc_ids: list) void
        +run() void
    }

    class LocalRunner {
        -INPUT_DIR : str
        -OUTPUT_FILE : str
        +load_documents() dict~str, list~
        +map_phase(doc_id: str, lines: list) list~tuple~
        +sort_phase(pairs: list) list~tuple~
        +reduce_phase(pairs: list) dict~str, list~
        +run() void
    }

    class InvertedIndex {
        <<output>>
        -index : dict~str, list~str~~
        +lookup(word: str) list~str~
        +to_file(path: str) void
    }

    class HadoopStreaming {
        <<external>>
        +submit_job(mapper: str, reducer: str) void
        +hdfs_put(local: str, remote: str) void
        +hdfs_get(remote: str, local: str) void
    }

    Mapper --> InvertedIndex : emite perechi intermediare
    Reducer --> InvertedIndex : produce index final
    LocalRunner --> Mapper : apeleaza logica de mapare
    LocalRunner --> Reducer : apeleaza logica de reducere
    LocalRunner --> InvertedIndex : scrie output
    HadoopStreaming --> Mapper : ruleaza ca subprocess
    HadoopStreaming --> Reducer : ruleaza ca subprocess
    HadoopStreaming --> InvertedIndex : scrie in HDFS
```

## Descriere clase

### `Mapper` (`mapper_inverted_index.py`)
Citeste linii din `stdin`, curata cuvintele (lowercase, fara punctuatie) si emite perechi `(cuvant, document_id)` pe `stdout`. Stie `document_id` din variabila de mediu `map_input_file`.

### `Reducer` (`reducer_inverted_index.py`)
Citeste perechi sortate din `stdin`, le grupeaza pe cheie (cuvant) si deduplica `document_id`-urile. Emite `(cuvant, [doc1, doc2, ...])` pe `stdout`.

### `LocalRunner` (`run_local.py`)
Simuleaza intregul pipeline MapReduce in Python pur, fara Hadoop. Apeleaza logica de mapare si reducere direct, fara subprocesse sau pipe-uri.

### `InvertedIndex` (structura de date finala)
Dictionar `word -> [doc_id_1, doc_id_2, ...]`. Reprezinta output-ul final al algoritmului, scris in `output_local.txt` sau `part-00000` (Hadoop).

### `HadoopStreaming` (sistem extern)
Componenta externa Apache Hadoop care orchestreaza rularea distribuita a mapper-ului si reducer-ului prin `hadoop-streaming*.jar`.
