@echo off
REM SUVI Google Cloud Setup Script

echo ========================================
echo   🚀 SUVI Google Cloud Setup
echo ========================================
echo.

where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Google Cloud SDK not found!
    echo Please install from: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

echo Step 1: Setting up GCP Project...
echo.

set /p PROJECT_ID="Enter your GCP Project ID (or press Enter to create a new one): "

REM Jump past the new project creation if an ID was entered
if not "%PROJECT_ID%"=="" goto SkipNewProject

echo Creating new project...
set PROJECT_ID=suvi-hackathon-%RANDOM%
call gcloud projects create %PROJECT_ID% --name="SUVI Hackathon"

echo.
echo [CRITICAL] To enable APIs, this new project needs a Billing Account!
set /p BILLING_ID="Enter your Billing Account ID (leave blank to skip): "
if "%BILLING_ID%"=="" goto NoBilling
call gcloud beta billing projects link %PROJECT_ID% --billing-account=%BILLING_ID%
goto SkipNewProject

:NoBilling
echo [WARNING] You MUST go to the Google Cloud Console and link a billing account to %PROJECT_ID% before APIs will enable!
pause

:SkipNewProject
echo.
echo Using Project ID: %PROJECT_ID%
echo.

echo Step 2: Setting project as default...
call gcloud config set project %PROJECT_ID%

echo.
echo Step 3: Enabling required APIs...
echo This may take a few minutes. Grab some coffee...

call gcloud services enable cloudbuild.googleapis.com run.googleapis.com firestore.googleapis.com pubsub.googleapis.com bigquery.googleapis.com aiplatform.googleapis.com secretmanager.googleapis.com cloudfunctions.googleapis.com container.googleapis.com containerregistry.googleapis.com monitoring.googleapis.com logging.googleapis.com artifactregistry.googleapis.com

echo.
echo Step 4: Creating service account...
call gcloud iam service-accounts create suvi-agent --display-name="SUVI Agent Service Account" --description="Service account for SUVI agents"

echo.
echo Step 5: Assigning roles to service account...
for %%R in (roles/aiplatform.user roles/firestore.user roles/pubsub.publisher roles/pubsub.subscriber roles/bigquery.dataEditor roles/secretmanager.secretAccessor roles/logging.logWriter roles/monitoring.metricWriter) do call gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="%%R"

echo.
echo Step 6: Creating Firestore database...
call gcloud firestore databases create --location=asia-south1 --type=firestore-native

echo.
echo Step 7: Creating Pub/Sub topics...
call gcloud pubsub topics create suvi-actions
call gcloud pubsub topics create suvi-agents
call gcloud pubsub topics create suvi-telemetry

echo.
echo Step 8: Creating secrets...
call gcloud secrets create VERTEX_API_KEY --replication-policy=automatic || echo Secret may already exist
call gcloud secrets create GEMINI_API_KEY --replication-policy=automatic || echo Secret may already exist

echo.
echo Step 9: Setting up Application Default Credentials...
call gcloud auth application-default login

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