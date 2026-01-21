#!/bin/bash
set -e

echo "Notifying Slack about ingestion for collection: $NEXUS_COLLECTION"

if [ -n "$SLACK_WEBHOOK_URL" ]; then
  payload="{
    \"text\": \"Nexus RAG: Starting ingestion for collection '$NEXUS_COLLECTION' ($NEXUS_FILES)\",
    \"username\": \"Nexus Bot\",
    \"icon_emoji\": \":robot_face:\"
  }"

  curl -X POST -H 'Content-Type: application/json' \
    -d "$payload" \
    "$SLACK_WEBHOOK_URL"
else
  echo "SLACK_WEBHOOK_URL not set, skipping notification"
fi
