#!/bin/bash
set -e

echo "Logging ingestion metrics..."

log_file="/app/data/ingestion-metrics.log"

echo "=== Ingestion Complete ===" >> "$log_file"
echo "Timestamp: $(date -Iseconds)" >> "$log_file"
echo "Collection: $NEXUS_COLLECTION" >> "$log_file"
echo "Processed: $NEXUS_PROCESSED_COUNT" >> "$log_file"
echo "Skipped: $NEXUS_SKIPPED_COUNT" >> "$log_file"
echo "Failed: $NEXUS_FAILED_COUNT" >> "$log_file"

total=$((NEXUS_PROCESSED_COUNT + NEXUS_SKIPPED_COUNT + NEXUS_FAILED_COUNT))
echo "Total files: $total" >> "$log_file"
echo "" >> "$log_file"

echo "Metrics logged to $log_file"
