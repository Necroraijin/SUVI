#!/bin/bash
# infrastructure/deploy_gateway.sh

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="suvi-gateway"

echo "🚀 Deploying SUVI Gateway to Cloud Run in project: $PROJECT_ID"

cd apps/gateway

# Build the image using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --min-instances 1

echo "✅ Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
