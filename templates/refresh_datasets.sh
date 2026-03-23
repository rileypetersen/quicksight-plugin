#!/usr/bin/env bash
# Refresh all SPICE datasets for a QuickSight analysis.
# Usage: ./refresh_datasets.sh --account-id 123456789012 --profile production
#
# Add your dataset IDs to the DATASETS array below.

set -euo pipefail

ACCOUNT_ID=""
PROFILE="default"
REGION=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --account-id) ACCOUNT_ID="$2"; shift 2 ;;
    --profile)    PROFILE="$2"; shift 2 ;;
    --region)     REGION="$2"; shift 2 ;;
    *)            echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$ACCOUNT_ID" ]]; then
  echo "Error: --account-id is required"
  exit 1
fi

# Add your dataset IDs here
DATASETS=(
  # "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  # "ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj"
)

if [[ ${#DATASETS[@]} -eq 0 ]]; then
  echo "No datasets configured. Edit this script and add IDs to the DATASETS array."
  exit 1
fi

TIMESTAMP=$(date +%s)

for ds in "${DATASETS[@]}"; do
  echo "Refreshing dataset: $ds"
  aws quicksight create-ingestion \
    --aws-account-id "$ACCOUNT_ID" \
    --profile "$PROFILE" \
    ${REGION:+--region "$REGION"} \
    --data-set-id "$ds" \
    --ingestion-id "manual-${TIMESTAMP}-${ds}"
done

echo "Triggered refresh for ${#DATASETS[@]} dataset(s)."
echo "Check status with: aws quicksight describe-ingestion --aws-account-id $ACCOUNT_ID --profile $PROFILE --data-set-id <ID> --ingestion-id manual-${TIMESTAMP}-<ID>"
