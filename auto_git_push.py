import subprocess
from datetime import datetime

# Timestamp
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_msg = f"Automated backup: {now} (adding data points)."

# Git commands
commands = [
    "git add .",
    f'git commit -m "{commit_msg}"',
    "git push"
]

# Run each command
for cmd in commands:
    subprocess.run(cmd, shell=True)
