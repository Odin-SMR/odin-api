#!/bin/bash

# Base URL
BASE_URL="https://donnees-data.asc-csa.gc.ca/users/OpenData_DonneesOuvertes/pub/OSIRIS/Data_format%20netCDF/Level2/daily"

# Local download root directory
DOWNLOAD_DIR="osiris_l2_downloads"

# Create base directory
mkdir -p "$DOWNLOAD_DIR"

# Download the top-level directory HTML
INDEX_HTML=$(curl -s "$BASE_URL/")

# Extract subdirectory names like 200202/, 201306/, etc.
FOLDERS=$(echo "$INDEX_HTML" | grep -oE 'href="[0-9]{6}/"' | cut -d'"' -f2)

# Loop over each folder
for folder in $FOLDERS; do
  echo "Checking folder: $folder"

  # Download that month's index page
  FOLDER_INDEX=$(curl -s "$BASE_URL/$folder")

  # Extract only filenames that match the required pattern
  FILES=$(echo "$FOLDER_INDEX" | grep -oE 'OSIRIS-Odin_L2-O3-Limb-MART_v5-07_[^"]+\.he5')

  for file in $FILES; do
    FILE_URL="$BASE_URL/$folder$file"
    LOCAL_DIR="$DOWNLOAD_DIR/$folder"
    LOCAL_PATH="$LOCAL_DIR/$file"

    # Make sure local YYYYMM/ directory exists
    mkdir -p "$LOCAL_DIR"

    # Only download if file doesn't exist already
    if [ ! -f "$LOCAL_PATH" ]; then
      echo "Downloading $FILE_URL -> $LOCAL_PATH"
      wget -q -O "$LOCAL_PATH" "$FILE_URL"
    else
      echo "Already exists: $LOCAL_PATH"
    fi
  done
done

echo "✅ Done downloading L2-O3-Limb-MART_v5-07 files."
