import logging
import os
import subprocess
import time
from pathlib import Path

import requests

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_EMAIL = os.getenv("GITHUB_EMAIL")
GITHUB_ORG = os.getenv("MAI_GITHUB_ORG")
GITHUB_API_BASE_URL = "https://api.github.com"


DEBUG = os.getenv("DEBUG", False)
quiet = "-q" if DEBUG else ""


def get_remote_url(repo_name):
    return f"https://{GITHUB_ORG}:{GITHUB_ACCESS_TOKEN}@github.com/{GITHUB_ORG}/{repo_name}.git"


def create_github_repo(repo_path: Path, repo_name: str):
    logging.info("[INFO] Creating GitHub repo...")

    # configure git users
    subprocess.run(f"git config --global user.name {GITHUB_USERNAME}".split())
    subprocess.run(f"git config --global user.email {GITHUB_EMAIL}".split())

    # Initialize a Git repository
    subprocess.run(f"git init {quiet}".split(), cwd=str(repo_path))

    # Commit the changes
    subprocess.run("git add . ".split(), cwd=str(repo_path))
    subprocess.run(
        f"git commit {quiet} -m".split() + ["Initial commit"], cwd=str(repo_path)
    )

    # Create a new repository on GitHub
    response = requests.post(
        f"{GITHUB_API_BASE_URL}/orgs/{GITHUB_ORG}/repos",
        json={
            "name": repo_name,
            "private": True,
        },
        auth=(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN),
    )
    response.raise_for_status()

    time.sleep(3)

    # Add the GitHub remote to the local Git repository and push the changes
    remote_url = get_remote_url(repo_name)
    subprocess.run(
        f"git remote add origin {remote_url}", cwd=str(repo_path), shell=True
    )
    # rename default branch to main
    subprocess.run("git branch -M main".split(), cwd=str(repo_path))
    subprocess.run(f"git push {quiet} -u origin main".split(), cwd=str(repo_path))

    return response.json()["html_url"]


def commit_to_orphan_branch(repo_path, new_branch, files_to_add, commit_message):
    """
    Create an orphan branch in a Git repository, add files, commit, and push.

    Parameters:
    - repo_path: Path to the local Git repository.
    - new_branch: Name of the orphan branch to create.
    - files_to_add: List of file paths to add to the new branch.
    - commit_message: Commit message.
    """

    # Change to the repository directory
    os.chdir(repo_path)

    # Create the orphan branch
    subprocess.run(["git", "checkout", "--orphan", new_branch], check=True)

    # Clear the working directory
    subprocess.run(["git", "rm", "-rf", "."], check=True)

    # Add the specified files
    for file in files_to_add:
        subprocess.run(["git", "add", file], check=True)

    # Commit the changes
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Push the branch to the remote repository
    subprocess.run(["git", "push", "origin", new_branch], check=True)


def repo_exists(repo_name):
    repo_url = f"{GITHUB_API_BASE_URL}/repos/{GITHUB_ORG}/{repo_name}"
    r = requests.get(repo_url, auth=(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN))
    return r.status_code == 200


def clone_repo(repo_name: str, output_dir: Path):
    remote_url = get_remote_url(repo_name)
    subprocess.run(["git", "clone", remote_url, output_dir], check=True)
    return output_dir / repo_name
