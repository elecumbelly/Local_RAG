#!/bin/bash
set -e

echo "Validating PDF files before ingestion..."

IFS=',' read -ra files <<< "$NEXUS_FILES"

invalid_count=0
for file in "${files[@]}"; do
  if [[ ! "$file" == *.pdf ]]; then
    echo "ERROR: File $file is not a PDF"
    ((invalid_count++))
  fi

  if [[ ! -f "$file" ]]; then
    echo "ERROR: File $file does not exist"
    ((invalid_count++))
  fi

  file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
  if [[ $file_size -gt 104857600 ]]; then
    echo "WARNING: File $file is larger than 100MB"
  fi
done

if [[ $invalid_count -gt 0 ]]; then
  echo "SKIP:$invalid_count invalid PDF file(s) found"
  exit 1
fi

echo "All PDFs valid, proceeding with ingestion"
