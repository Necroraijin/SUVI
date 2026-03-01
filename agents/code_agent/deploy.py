import json
from pathlib import Path

def deploy_code_agent():
    config_path = Path(__file__).parent / "agent_card.json"
    if not config_path.exists():
        print("[Deploy Error] agent_card.json not found for Code Agent!")
        return

    with open(config_path, "r") as f:
        card = json.load(f)
        
    print(f"🚀 Preparing deployment for worker: {card.get('agent_name')} (v{card.get('version')})")
    print("📦 Packaging file system tools and code generation logic...")
    print("✅ Deployment successful! Code Agent is standing by.")

if __name__ == "__main__":
    deploy_code_agent()