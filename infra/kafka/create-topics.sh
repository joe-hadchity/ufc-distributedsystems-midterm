#!/bin/bash
set -euo pipefail

BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-broker:9092}

# Helper: create topic if not exists
create_topic() {
  local name="$1"
  local partitions="$2"
  local retention_ms="$3"
  if kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER" --list | grep -q "^${name}$"; then
    echo "Topic exists: ${name}"
  else
    echo "Creating topic: ${name}"
    kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER" \
      --create --topic "$name" \
      --partitions "$partitions" --replication-factor 1
    kafka-configs.sh --bootstrap-server "$BOOTSTRAP_SERVER" \
      --alter --topic "$name" --add-config retention.ms=${retention_ms}
  fi
}

# Wait for broker
until kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER" --list >/dev/null 2>&1; do
  echo "Waiting for Kafka broker at $BOOTSTRAP_SERVER ..."
  sleep 3
done

# Topics and policies
# urls: short-lived queue of URLs
create_topic urls 3 $((24*60*60*1000))          # 1 day
# html: raw HTML pages
create_topic html 3 $((7*24*60*60*1000))        # 7 days
# clean: cleaned/normalized docs
create_topic clean 3 $((14*24*60*60*1000))      # 14 days
# embed: chunks to embed
create_topic embed 3 $((7*24*60*60*1000))       # 7 days
# dlq: failures retained longer
create_topic dlq 3 $((14*24*60*60*1000))        # 14 days

echo "Kafka topics initialized."


