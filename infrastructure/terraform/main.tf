terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud APIs
resource "google_project_service" "firestore" {
  project            = var.project_id
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# 2. Setup Firestore (Long Term Memory)
resource "google_firestore_database" "suvi_memory" {
  project     = var.project_id
  name        = "(default)" # Required for the default database
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

# 3. Setup Secret Manager (For Vertex AI Key)
resource "google_secret_manager_secret" "vertex_key" {
  secret_id = "vertex-ai-key-${var.environment}"
  
  replication {
    auto {} # Automatically replicate the secret across Google's network
  }

  depends_on = [google_project_service.secretmanager]
}