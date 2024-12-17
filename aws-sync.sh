#!/bin/bash
PATH=/usr/bin:/usr/local/bin

# Set the source and destination buckets
SOURCE_BUCKET="s3://bahaimedia"
DEST_BUCKETS=("s3://bahaimedia-eu" "s3://bahaimedia-sg" "s3://bahaimedia-sp")

# Path to the needsync.txt file
NEEDSYNC_FILE="/var/log/mediawiki/needsync.txt"

# Check if needsync.txt exists
if [ ! -f "$NEEDSYNC_FILE" ]; then
    exit 1
fi

# Read the file line by line
while IFS= read -r FILE_PATH || [[ -n "$FILE_PATH" ]]; do
    # Skip empty lines and comments
    [[ -z "$FILE_PATH" || "$FILE_PATH" =~ ^\s*# ]] && continue

    # Trim whitespace
    FILE_PATH=$(echo "$FILE_PATH" | xargs)

    # Sync the file to each destination bucket
    for DEST_BUCKET in "${DEST_BUCKETS[@]}"; do
        aws s3 cp "$SOURCE_BUCKET/$FILE_PATH" "$DEST_BUCKET/${FILE_PATH%/*}/"
    done
done < "$NEEDSYNC_FILE"

# Delete the needsync.txt file after the process
rm -f "$NEEDSYNC_FILE"
