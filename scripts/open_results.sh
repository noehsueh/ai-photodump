#!/bin/bash

# Read the ranked categories JSON file
json_file="output/ranked_categories.json"

# Check if the file exists
if [ ! -f "$json_file" ]; then
    echo "Error: $json_file not found"
    exit 1
fi

# For each category and image in the JSON, open the image
cat "$json_file" | jq -r 'to_entries[] | "\(.key)\t\(.value | keys[])"' | while IFS=$'\t' read -r category image; do
    echo "Opening $image from category: $category"
    # Use xdg-open on Linux, open on macOS, or start on Windows
    if command -v xdg-open &> /dev/null; then
        xdg-open "$image" &
    elif command -v open &> /dev/null; then
        open "$image" &
    elif command -v start &> /dev/null; then
        start "$image" &
    else
        echo "No compatible open command found"
        exit 1
    fi
done
