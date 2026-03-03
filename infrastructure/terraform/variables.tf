variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The region to deploy resources (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The deployment environment (dev or prod)"
  type        = string
}