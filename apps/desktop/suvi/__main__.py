import sys
import os

# Ensure the root suvi directory is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.desktop.suvi.app import run_app

if __name__ == "__main__":
    run_app()