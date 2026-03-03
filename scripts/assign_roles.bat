@echo off
REM SUVI GCP Role Assignment Script
REM Run this after creating the service account

set PROJECT_ID=%1
if "%PROJECT_ID%"=="" set PROJECT_ID=suvi-hackathon-YOURNAME

echo Assigning roles to service account...
echo Project: %PROJECT_ID%

echo Assigning aiplatform.user...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/aiplatform.user"

echo Assigning firestore.user...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/firestore.user"

echo Assigning pubsub.publisher...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/pubsub.publisher"

echo Assigning pubsub.subscriber...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/pubsub.subscriber"

echo Assigning bigquery.dataEditor...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"

echo Assigning secretmanager.secretAccessor...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:suvi-agent@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

echo.
echo All roles assigned!
pause
