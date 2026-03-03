@echo off
REM SUVI Google Cloud Setup Script
REM Run this script to set up GCP for your hackathon project

echo ========================================
echo   🚀 SUVI Google Cloud Setup
echo ========================================
echo.

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Google Cloud SDK not found!
    echo Please install from: https://cloud.google.com/sdk/docs/install
    echo Then run: gcloud init
    exit /b 1
)

echo Step 1: Setting up GCP Project...
echo.

set /p PROJECT_ID=Enter your GCP Project ID (or press Enter to create a new one):

if "%PROJECT_ID%"=="" (
    echo Creating new project...
    set PROJECT_ID=suvi-hackathon-%RANDOM%
    gcloud projects create %PROJECT_ID% --name="SUVI Hackathon"
    
    echo.
    echo [CRITICAL] To enable APIs, this new project needs a Billing Account!
    set /p BILLING_ID=Enter your Billing Account ID (leave blank to skip and link manually later):
    if not "%BILLING_ID%"=="" (
        gcloud beta billing projects link %PROJECT_ID% --billing-account=%BILLING_ID%
    ) else (
        echo [WARNING] You MUST go to the Google Cloud Console and link a billing account to %PROJECT_ID% before APIs will enable!
        pause
    )
)

echo.
echo Using Project ID: %PROJECT_ID%
echo.

echo Step 2: Setting project as default...
gcloud config set project %PROJECT_ID%

echo.
echo Step 3: Enabling required APIs...
echo This may take a few minutes. Grab some coffee...

gcloud services enable ^
    cloudbuild.googleapis.com ^
    run.googleapis.com ^
    firestore.googleapis.com ^
    pubsub.googleapis.com ^
    bigquery.googleapis.com ^
    aiplatform.googleapis.com ^
    secretmanager.googleapis.com ^
    cloudfunctions.googleapis.com ^
    container.googleapis.com ^
    containerregistry.googleapis.com ^
    monitoring.googleapis.com ^
    logging.googleapis.com ^
    artifactregistry.googleapis.com

echo.
echo Step 4: Creating service account...
gcloud iam service-accounts create suvi-agent ^
    --display-name="SUVI Agent Service Account" ^
    --description="Service account for SUVI agents"

echo.
echo Step 5: Assigning roles to service account...
REM Removed quotes from list to prevent batch syntax errors
for %%R in (
    roles/aiplatform.user
    roles/firestore.user
    roles/pubsub.publisher
    roles/pubsub.subscriber
    roles/bigquery.dataEditor
    roles/secretmanager.secretAccessor
    roles/logging.logWriter
    roles/monitoring.metricWriter
) do (
    gcloud projects add-iam-policy-binding %PROJECT_ID% ^
        --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" ^
        --role="%%R"
)

echo.
echo Step 6: Creating Firestore database...
gcloud firestore databases create ^
    --location=asia-south1 ^
    --type=firestore-native

echo.
echo Step 7: Creating Pub/Sub topics...
gcloud pubsub topics create suvi-actions
gcloud pubsub topics create suvi-agents
gcloud pubsub topics create suvi-telemetry

echo.
echo Step 8: Creating secrets...
echo Creating initial secrets in Secret Manager...

gcloud secrets create VERTEX_API_KEY --replication-policy=automatic || echo Secret may already exist
gcloud secrets create GEMINI_API_KEY --replication-policy=automatic || echo Secret may already exist

echo.
echo Step 9: Setting up Application Default Credentials...
gcloud auth application-default login

echo.
echo ========================================
echo   ✅ Setup Complete!
echo ========================================
echo.
echo Project ID: %PROJECT_ID%
echo Region: asia-south1 (Mumbai)
echo.
echo Next steps:
echo 1. Set environment variables (Run these in your current terminal):
echo     set GCP_PROJECT=%PROJECT_ID%
echo     set GCP_LOCATION=asia-south1
echo.
echo 2. Build and deploy the gateway:
echo     gcloud builds submit --config=cloudbuild.yaml
echo.
echo 3. Run SUVI locally:
echo     python -m apps.desktop.suvi.__main__
echo.
pause