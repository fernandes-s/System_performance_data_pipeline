from pathlib import Path
import subprocess
from datetime import datetime
import os

# Ensure script always runs from project root
BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)

# Timestamp
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_msg = f"Automated backup: {now} (adding data points)."

# Git commands
commands = [
    ["git", "add", "."],
    ["git", "commit", "-m", commit_msg],
    ["git", "push"]
]

# Run each command
for cmd in commands:
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running: {' '.join(cmd)}")
        print(result.stderr)
    else:
        print(result.stdout)