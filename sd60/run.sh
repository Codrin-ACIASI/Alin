#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_PIPE="$SCRIPT_DIR/output_pipe.txt"
OUTPUT_LOCAL="$SCRIPT_DIR/output_local.txt"
MAPPER="$SCRIPT_DIR/src/mapper_inverted_index.py"
REDUCER="$SCRIPT_DIR/src/reducer_inverted_index.py"
RUN_LOCAL="$SCRIPT_DIR/src/run_local.py"

echo "=================================================="
echo "  SPLSD-60: Indexed Inverted Index - MapReduce"
echo "=================================================="
echo ""

if ! command -v python3 &>/dev/null; then
    echo "[EROARE] python3 nu este instalat."
    echo "         Instaleaza cu: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
if [ "$PYTHON_VERSION" -lt 36 ]; then
    echo "[EROARE] Python 3.6+ este necesar. Versiunea detectata este prea veche."
    exit 1
fi

echo "[OK] Python3 gasit: $(python3 --version)"

if [ ! -d "$INPUT_DIR" ] || [ -z "$(ls -A "$INPUT_DIR" 2>/dev/null)" ]; then
    echo "[EROARE] Directorul input/ este gol sau nu exista."
    echo "         Adauga fisiere .txt in $INPUT_DIR"
    exit 1
fi

echo "[OK] Director input gasit cu $(ls "$INPUT_DIR" | wc -l) fisiere."

chmod +x "$MAPPER"
chmod +x "$REDUCER"

echo ""
echo "--- METODA 1: Rulare locala (Python pur) ---"
python3 "$RUN_LOCAL"
echo ""

echo "--- METODA 2: Rulare prin pipe (simulare Hadoop Streaming) ---"
rm -f "$OUTPUT_PIPE"

(
    for f in "$INPUT_DIR"/*.txt; do
        export map_input_file="$f"
        cat "$f" | python3 "$MAPPER"
    done
) | sort | python3 "$REDUCER" > "$OUTPUT_PIPE"

WORD_COUNT=$(wc -l < "$OUTPUT_PIPE")
echo "[OK] Inverted Index generat: $WORD_COUNT cuvinte unice indexate."
echo "[OK] Output pipe salvat in: $OUTPUT_PIPE"
echo ""

echo "=== TOP 10 cuvinte indexate (pipe output) ==="
head -10 "$OUTPUT_PIPE"

echo ""
echo "=================================================="
echo "  Rulare completa cu succes!"
echo "  - output_local.txt  (simulare Python)"
echo "  - output_pipe.txt   (simulare Hadoop Streaming)"
echo "=================================================="
echo ""

if command -v hadoop &>/dev/null; then
    echo "[INFO] Hadoop detectat pe sistem. Pentru rulare distribuita, consulta README.md."
else
    echo "[INFO] Hadoop nu este instalat. Rezultatele de mai sus sunt generate local."
fi
