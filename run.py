"""
Root launcher for Icon Changer.
Run with: python run.py
Or with arguments: python run.py --quick "C:\\path\\to\\folder"
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from icon_changer.main import main

if __name__ == "__main__":
    main()
