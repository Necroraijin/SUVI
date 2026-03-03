"""
SUVI Google Cloud Setup Guide
=============================

This guide walks you through setting up Google Cloud for SUVI,
optimized for Mumbai (asia-south1) with global access for hackathon judges.

PREREQUISITES
-------------
1. Google Account with billing enabled
2. gcloud CLI installed: https://cloud.google.com/sdk/docs/install
3. Python 3.12+ installed

STEP 1: Create GCP Project
--------------------------
Option A: Via Console (Recommended)
1. Go to https://console.cloud.google.com/projectcreate
2. Enter project name: suvi-hackathon-YOURNAME
3. Select organization (or leave as No organization)
4. Click Create

Option B: Via CLI
  gcloud projects create suvi-hackathon-YOURNAME

STEP 2: Enable APIs
-------------------
Run these commands in your terminal:

  gcloud config set project suvi-hackathon-YOURNAME

  gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudfunctions.googleapis.com \
    artifactregistry.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

STEP 3: Set Up Authentication
------------------------------
1. For local development:
   gcloud auth application-default login

2. Create service account:
   gcloud iam service-accounts create suvi-agent \
     --display-name="SUVI Agent" \
     --description="Service account for SUVI agents"

3. Assign roles:
   for role in aiplatform.user firestore.user pubsub.publisher pubsub.subscriber bigquery.dataEditor secretmanager.secretAccessor; do
     gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:suvi-agent@$PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/$role"
   done

4. Download service account key (optional, for local dev):
   gcloud iam service-accounts keys create key.json \
     --iam-account=suvi-agent@$PROJECT_ID.iam.gserviceaccount.com

   Set environment variable:
   export GOOGLE_APPLICATION_CREDENTIALS=key.json

STEP 4: Create Firestore Database
---------------------------------
gcloud firestore databases create --location=asia-south1 --type=firestore-native

STEP 5: Create Pub/Sub Topics
------------------------------
gcloud pubsub topics create suvi-actions
gcloud pubsub topics create suvi-agents
gcloud pubsub topics create suvi-telemetry

STEP 6: Create Secrets
-----------------------
echo -n "your-vertex-api-key" | gcloud secrets create VERTEX_API_KEY --replication-policy=automatic --data-file=-
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --replication-policy=automatic --data-file=-

STEP 7: Set Environment Variables
----------------------------------
Create a .env file:

  GCP_PROJECT=suvi-hackathon-YOURNAME
  GCP_LOCATION=asia-south1
  VERTEX_API_KEY=your-vertex-api-key
  GEMINI_API_KEY=your-gemini-api-key
  SUVI_CLIENT_TOKEN=suvi-hackathon-secret-123

STEP 8: Deploy Gateway to Cloud Run
------------------------------------
From the SUVI root directory:

  cd apps/gateway

  # Build and deploy
  gcloud run deploy suvi-gateway \
    --source . \
    --region asia-south1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account suvi-agent@$PROJECT_ID.iam.gserviceaccount.com

  Note: Use --allow-unauthenticated for the hackathon so judges can access!

STEP 9: Get Your Deployment URL
-------------------------------
After deployment, you'll see a URL like:
  https://suvi-gateway-xxxxx.asia-south1.run.app

This URL works globally - judges anywhere can access it!

STEP 10: Test Locally
---------------------
To run the desktop app locally:

  pip install -e .
  python -m apps.desktop.suvi

For the gateway locally:

  pip install -r apps/gateway/requirements.txt
  uvicorn apps.gateway.suvi_gateway.main:app --reload --port 8080

TROUBLESHOOTING
---------------

Q: Judges can't access my app
A: Make sure you deployed with --allow-unauthenticated
   Check Cloud Run console to see if service is running

Q: Getting authentication errors
A: Verify GOOGLE_APPLICATION_CREDENTIALS points to your service account key
   Or run: gcloud auth application-default login

Q: Vertex AI not available in Mumbai
A: Vertex AI is available in us-central1 (Iowa)
   Set GCP_LOCATION=us-central1 in your .env
   Traffic will route to nearest region automatically

Q: Need to update the app for judges
A: Redeploy with:
   gcloud run deploy suvi-gateway --source . --region asia-south1

Q: Want to add API key protection
A: Remove --allow-unauthenticated and add:
   gcloud run deploy suvi-gateway ... --auth-endpoint=login

OPTIMIZATION FOR JUDGES
-----------------------
For best global experience:

1. Use Cloud CDN with Cloud Run:
   - Go to Cloud Run > your service > Edit
   - Enable Cloud CDN

2. Set up custom domain (optional):
   - Cloud Run > Domains > Add mapping
   - Connect your custom domain

3. Monitor with Cloud Monitoring:
   - Console > Monitoring > Dashboards
   - See latency, errors, request counts

QUICK COMMANDS
--------------
# Check project
gcloud config get-value project

# Check enabled APIs
gcloud services list --enabled

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# View Cloud Run service
gcloud run services describe suvi-gateway --region asia-south1

# Delete (after hackathon)
gcloud run services delete suvi-gateway --region asia-south1
"""

# Save as text file as well
with open("SUVI_GCP_SETUP.txt", "w") as f:
    f.write(__doc__)

print(__doc__)
