import os
import subprocess
import sys

# Default GCP project settings (override via env vars)
GCP_PROJECT = os.environ.get("GCP_PROJECT", "suvi-project")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")
SERVICE_PREFIX = "suvi-"

def run_command(cmd, cwd=None):
    """Utility to run shell commands safely."""
    try:
        subprocess.run(cmd, check=True, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)

def deploy_agent(agent_name, agents_dir):
    """Deploys an individual agent as a Cloud Run service."""
    agent_path = os.path.join(agents_dir, agent_name)
    
    # Check if agent has a deployable structure (needs a main/app file or Dockerfile)
    if not os.path.isdir(agent_path) or agent_name == "shared":
        return

    print(f"\n--- Deploying {agent_name.upper()} ---")
    
    service_name = f"{SERVICE_PREFIX}{agent_name.replace('_', '-')}"
    
    # For a real deployment, we assume a Dockerfile exists in the root or agent folder.
    # Alternatively, we can use Google Cloud buildpacks to deploy from source.
    # We will use source-based deployment for simplicity.
    
    print(f"🚀 Deploying {service_name} to Cloud Run in {GCP_REGION}...")
    
    deploy_cmd = (
        f"gcloud run deploy {service_name} "
        f"--source {agent_path} "
        f"--region {GCP_REGION} "
        f"--project {GCP_PROJECT} "
        f"--allow-unauthenticated "
        f"--set-env-vars GCP_PROJECT={GCP_PROJECT} "
        f"--quiet"
    )
    
    # In a local hackathon environment without gcloud configured, this will fail.
    # We will wrap it in a try-catch to allow local mock testing if gcloud is missing.
    try:
        subprocess.run(deploy_cmd, check=True, shell=True)
        print(f"✅ {agent_name.upper()} successfully deployed.")
    except subprocess.CalledProcessError:
        print(f"⚠️ Failed to deploy {agent_name} to Cloud Run.")
        print("💡 Ensure 'gcloud' CLI is installed, authenticated, and billing is enabled.")
        print(f"💡 Command attempted: {deploy_cmd}")

def deploy_all():
    print("🚀 Initiating global deployment of all SUVI agents to Google Cloud Run...")
    
    agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
    
    if not os.path.exists(agents_dir):
        print(f"❌ Error: Could not find agents directory at {agents_dir}")
        sys.exit(1)

    for agent_name in os.listdir(agents_dir):
        deploy_agent(agent_name, agents_dir)

    print("\n✅ Global Agent deployment sequence completed.")

if __name__ == "__main__":
    deploy_all()
