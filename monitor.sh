#!/bin/bash

subjd=$1
if [ -z "$subjd" ]; then
    subjd="unknown"
fi

LOG_FILE="resource_usage_${subjd}.log"

echo "Timestamp,CPU_Usage(%),Mem_Usage(%)" > "$LOG_FILE"

while true; do
  cpu_usage=$(top -bn1 | awk '/Cpu\(s\)/ {print 100 - $8}')
  mem_usage=$(free | awk '/Mem:/ {print $3/$2 * 100.0}')

  echo "$(date '+%Y-%m-%d %H:%M:%S'),$cpu_usage,$mem_usage" >> "$LOG_FILE"

  sleep 5
done
