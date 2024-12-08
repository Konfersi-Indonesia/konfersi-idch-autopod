#!/bin/bash

CONFIG_FILE=transfer-config.yaml
# Directory containing the archives (defaults to the current directory)
TARGET_DIR=${1:-.}

# Find all .tar.gz and .tar.bz2 files and extract them in parallel
find "$TARGET_DIR" -type f \( -name "*.tar.gz" -o -name "*.tar.bz2" \) | \
while read -r file; do
    extract_dir="${file%.*.*}_extracted"
    mkdir -p "$extract_dir"
    echo "tar -xvf \"$file\" -C \"$extract_dir\""
done | xargs -I{} -P "$(nproc)" bash -c '{}'

rm -r *.tar.bz2 *.tar.gz