#!/bin/bash
# infrastructure/setup_gcp.sh
# Run once: ./setup_gcp.sh your-project-id

PROJECT_ID=${1:-"suvi-hackathon-2025"}
REGION="us-central1"

echo "Setting up SUVI GCP project: $PROJECT_ID"

gcloud projects create $PROJECT_ID --name="SUVI Hackathon" 2>/dev/null || true
gcloud config set project $PROJECT_ID

# Enable all required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  firebase.googleapis.com \
  identitytoolkit.googleapis.com

# Create service account
gcloud iam service-accounts create suvi-sa \
  --display-name="SUVI Service Account"

SA_EMAIL="suvi-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles
for role in \
  roles/aiplatform.user \
  roles/datastore.user \
  roles/pubsub.publisher \
  roles/bigquery.dataEditor \
  roles/logging.logWriter \
  roles/secretmanager.secretAccessor \
  roles/storage.objectCreator; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" --role="$role" --quiet
done

# Download credentials
gcloud iam service-accounts keys create credentials.json \
  --iam-account=$SA_EMAIL

# Create Firestore database
gcloud firestore databases create --location=$REGION --type=firestore-native

# Create Pub/Sub topics
for topic in suvi-actions suvi-sessions suvi-telemetry suvi-dlq; do
  gcloud pubsub topics create $topic
done

# Create BigQuery dataset
bq mk --dataset --location=$REGION ${PROJECT_ID}:suvi_analytics

# Create Cloud Storage bucket for replays
gsutil mb -l $REGION gs://${PROJECT_ID}-suvi-replays

echo "GCP setup complete!"
echo "SA credentials saved to credentials.json"
echo "Set GOOGLE_APPLICATION_CREDENTIALS=./credentials.json"
