#!/bin/bash
# SUVI GCP Role Assignment Script

PROJECT_ID=${1:-suvi-hackathon-YOURNAME}
SERVICE_ACCOUNT="suvi-agent@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Assigning roles to service account..."
echo "Project: $PROJECT_ID"
echo ""

# Array of roles
ROLES=(
    "roles/aiplatform.user"
    "roles/firestore.user"
    "roles/pubsub.publisher"
    "roles/pubsub.subscriber"
    "roles/bigquery.dataEditor"
    "roles/secretmanager.secretAccessor"
)

# Assign each role
for ROLE in "${ROLES[@]}"; do
    echo "Assigning $ROLE..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="$ROLE" 2>/dev/null || echo "  (already exists or error)"
done

echo ""
echo "All roles assigned!"
