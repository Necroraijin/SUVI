param (
    [string]$ProjectId = "suvi-hackathon-2025",
    [string]$Region = "us-central1"
)

Write-Host "Setting up SUVI GCP project: $ProjectId" -ForegroundColor Cyan

# Create project, ignore errors if it exists
gcloud projects create $ProjectId --name="SUVI Hackathon" 2>$null
gcloud config set project $ProjectId

Write-Host "Enabling Google Cloud APIs..." -ForegroundColor Yellow
gcloud services enable aiplatform.googleapis.com run.googleapis.com firestore.googleapis.com pubsub.googleapis.com bigquery.googleapis.com logging.googleapis.com secretmanager.googleapis.com storage.googleapis.com cloudbuild.googleapis.com firebase.googleapis.com identitytoolkit.googleapis.com

Write-Host "Creating Service Account..." -ForegroundColor Yellow
gcloud iam service-accounts create suvi-sa --display-name="SUVI Service Account"
$SaEmail = "suvi-sa@$ProjectId.iam.gserviceaccount.com"

$Roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/pubsub.publisher",
    "roles/bigquery.dataEditor",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectCreator"
)

Write-Host "Assigning IAM Roles..." -ForegroundColor Yellow
foreach ($Role in $Roles) {
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$SaEmail" --role="$Role" --quiet
}

Write-Host "Creating JSON Key (credentials.json)..." -ForegroundColor Yellow
gcloud iam service-accounts keys create credentials.json --iam-account=$SaEmail

Write-Host "Creating Firestore Database..." -ForegroundColor Yellow
gcloud firestore databases create --location=$Region --type=firestore-native

Write-Host "Creating Pub/Sub Topics..." -ForegroundColor Yellow
$Topics = @("suvi-actions", "suvi-sessions", "suvi-telemetry", "suvi-dlq")
foreach ($Topic in $Topics) {
    gcloud pubsub topics create $Topic
}

Write-Host "Creating BigQuery Dataset..." -ForegroundColor Yellow
bq mk --dataset --location=$Region "$ProjectId`:suvi_analytics"

Write-Host "Creating Cloud Storage Bucket..." -ForegroundColor Yellow
gsutil mb -l $Region "gs://$ProjectId-suvi-replays"

Write-Host "=========================================" -ForegroundColor Green
Write-Host "GCP Setup Complete!" -ForegroundColor Green
Write-Host "Service Account credentials saved to credentials.json" -ForegroundColor Green
Write-Host ""
Write-Host "CRITICAL NEXT STEP:" -ForegroundColor Red
Write-Host "Run this command in your PowerShell terminal to authenticate your local environment:" -ForegroundColor Cyan
Write-Host "`$env:GOOGLE_APPLICATION_CREDENTIALS='.\credentials.json'" -ForegroundColor White
