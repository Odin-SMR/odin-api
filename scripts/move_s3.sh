#!/bin/bash

# List of subfolders to copy
folders=(
  "HM_AC1c/"
  "HM_AC1d/"
  "HM_AC1e/"
  "IM_AC1c/"
  "IM_AC1de/"
  "IM_AC2ab/"
  "IM_AC2c/"
  "SM_AC1e/"
  "SM_AC2ab/"
)

# Base paths
source_base="s3://odin-smr/version_2.0"
destination_base="s3://odin-smr/SMRhdf/Qsmr-2-0"

# Loop over each folder and run the copy command
for folder in "${folders[@]}"; do
  echo "Copying $folder ..."
  aws s3 cp "${source_base}/${folder}" "${destination_base}/${folder}" \
    --recursive --profile odin-cdk --quiet
done

echo "All copies completed."