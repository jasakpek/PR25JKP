#!/bin/bash

# Preveri, ali je parameter za osnovno ime datoteke podan
if [[ -z "$1" ]]; then
    echo "Napaka: Podati morate osnovno ime datoteke (brez številke in razširitve)."
    echo "Uporaba: ./process_links.sh article_"
    exit 1
fi

# Osnovno ime datoteke
base_name="$1"

# Začetna številka datoteke
num=0

# Iteriraj skozi datoteke, dokler obstajajo
while true; do
    # Sestavi ime trenutne datoteke
    input_file="${base_name}${num}.txt"

    # Preveri, ali datoteka obstaja
    if [[ ! -f "$input_file" ]]; then
        echo "Ni več datotek za obdelavo. Zadnja obdelana številka: $((num - 1))"
        break
    fi

    echo "Obdelujem datoteko: $input_file"

    # Preberi vsako vrstico v trenutni datoteki
    while IFS= read -r link; do
        # Preveri, ali vrstica ni prazna
        if [[ -n "$link" ]]; then
	    echo -n "."
            python3 24ur_article_download_txt.py "$link" >> logs/download_to_txt.log
        fi
    done < "$input_file"

    # Povečaj številko za naslednjo datoteko
    num=$((num + 1))
done

echo "Končano."

