#!/bin/bash
DOMAIN=$1
if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain>"
  exit 1
fi

# Get timestamp from 7 days ago in ISO format
WEEK_AGO=$(date -d "7 days ago" -u +"%Y-%m-%dT%H:%M:%S")

# check for jq
if ! command -v jq &> /dev/null; then
    echo "jq could not be found, please install jq to run this script."
    exit 1
fi

# Get certificates issued in last 7 days
CURL_RESULT=$(curl -s "https://crt.sh/?q=${DOMAIN}&output=json&exclude=expired")
if [ -z "$CURL_RESULT" ]; then
  echo "No certificates found or error fetching data."
  exit 1
else
    echo "Fetched certificates from crt.sh"
fi

# Filter for Let's Encrypt certificates from last 7 days and deduplicate by serial number
RECENT_CERTS=$(echo "$CURL_RESULT" | \
  jq --arg week_ago "$WEEK_AGO" \
  '[.[] | select(.issuer_name | contains("Let'\''s Encrypt")) | select(.not_before >= $week_ago)] | 
   group_by(.serial_number) | map(.[0])')

echo "=== LET'S ENCRYPT RATE LIMIT CHECK ==="

# QUOTA 1: New Certificates per Registered Domain (50/week)
CERT_COUNT=$(echo "$RECENT_CERTS" | jq 'length')
echo "Certificates issued in last 7 days: $CERT_COUNT/50"
echo "   Remaining quota: $((50 - CERT_COUNT))"
if [ "$CERT_COUNT" -gt 40 ]; then
  echo "   WARNING: Approaching rate limit!"
fi
echo

# QUOTA 2: New Certificates per Exact Set of Identifiers (5/week)
echo "Exact identifier sets (5 certificates max per set):"
echo "$RECENT_CERTS" | \
  jq -r '.[] | .name_value | split("\n") | sort | join(",")' | \
  sort | uniq -c | \
  while read count domains; do
    if [ "$count" -gt 3 ]; then
      echo "   WARNING: $count/5: $domains"
    else
      echo "   $count/5: $domains"
    fi
  done
echo

# QUOTA 3: New Orders per Account (300/3hours) - Not trackable via crt.sh
echo "New Orders per Account (300/3hours): Not trackable via public logs"
echo "   This limit is per ACME account, not visible in certificate transparency"
echo

echo "Done."