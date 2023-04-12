import os
import subprocess
import sys
from pathlib import Path

import requests

repo_path = Path(sys.argv[1])
repo_name = repo_path.name

# Set up GitHub authentication
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_EMAIL = os.getenv("GITHUB_EMAIL")
GITHUB_ORG = os.getenv("MAI_GITHUB_ORG")
GITHUB_API_ENDPOINT = f"https://api.github.com/orgs/{GITHUB_ORG}/repos"

# configure git users
subprocess.run(f"git config --global user.name {GITHUB_USERNAME}", shell=True)
subprocess.run(f"git config --global user.email {GITHUB_EMAIL}", shell=True)

# Initialize a Git repository
subprocess.run("git init", cwd=str(repo_path), shell=True)
subprocess.run("git branch -m main", cwd=str(repo_path), shell=True)

# Commit the changes
subprocess.run("git add . ", cwd=str(repo_path), shell=True)
subprocess.run("git commit -m 'Initial commit'", cwd=str(repo_path), shell=True)

# Create a new repository on GitHub
response = requests.post(
    GITHUB_API_ENDPOINT,
    json={
        "name": repo_name,
        "private": True,
    },
    auth=(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN),
)
response.raise_for_status()

# Add the GitHub remote to the local Git repository and push the changes
remote_url = (
    f"https://{GITHUB_ORG}:{GITHUB_ACCESS_TOKEN}@github.com/MonlamAI/{repo_name}.git"
)
subprocess.run(f"git remote add origin {remote_url}", cwd=str(repo_path), shell=True)
subprocess.run("git push -u origin main", cwd=str(repo_path), shell=True)
