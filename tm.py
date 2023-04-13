import os
import random
import subprocess
import sys
from pathlib import Path

import requests

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_EMAIL = os.getenv("GITHUB_EMAIL")
GITHUB_ORG = os.getenv("MAI_GITHUB_ORG")
GITHUB_API_ENDPOINT = f"https://api.github.com/orgs/{GITHUB_ORG}/repos"

DEBUG = os.getenv("DEBUG", False)

quiet = "-q" if DEBUG else ""


def create_github_repo(repo_path: Path, repo_name: str):
    if DEBUG:
        print("[INFO] Creating GitHub repo...")

    # configure git users
    subprocess.run(f"git config --global user.name {GITHUB_USERNAME}", shell=True)
    subprocess.run(f"git config --global user.email {GITHUB_EMAIL}", shell=True)

    # Initialize a Git repository
    subprocess.run(f"git init {quiet}", cwd=str(repo_path), shell=True)

    # Commit the changes
    subprocess.run("git add . ", cwd=str(repo_path), shell=True)
    subprocess.run(
        f"git commit {quiet} -m 'Initial commit'", cwd=str(repo_path), shell=True
    )

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
    remote_url = f"https://{GITHUB_ORG}:{GITHUB_ACCESS_TOKEN}@github.com/MonlamAI/{repo_name}.git"
    subprocess.run(
        f"git remote add origin {remote_url}", cwd=str(repo_path), shell=True
    )
    # rename default branch to main
    subprocess.run("git branch -M main", cwd=str(repo_path), shell=True)
    subprocess.run(f"git push {quiet} -u origin main", cwd=str(repo_path), shell=True)

    return response.json()["html_url"]


def get_github_repo_name():
    """Generate TM Repo name"""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {GITHUB_ACCESS_TOKEN}",
    }

    def repo_exists(repo_name):
        url = f"{GITHUB_API_ENDPOINT}/{repo_name}"
        response = requests.get(url, headers=headers)
        return response.status_code == 200

    for _ in range(10000):  # Limit to a maximum number of attempts
        i = random.randint(1, 9999)
        repo_name = f"TM{str(i).zfill(4)}"
        if not repo_exists(repo_name):
            return repo_name

    raise Exception("Unable to find a unique repo name. Please try again.")


def convert_raw_align_to_tm(align_fn: Path, tm_path: Path):
    if DEBUG:
        print("[INFO] Conerting raw alignment to TM repo...")

    def bo_post_process(text: str):
        return text.replace("།།", "། །")

    def load_alignment(fn: Path):
        content = fn.read_text()
        if not content:
            return []

        for seg_pair in content.splitlines():
            if not seg_pair:
                continue

            if "\t" in seg_pair:
                try:
                    bo_seg, en_seg = seg_pair.split("\t", 1)
                except Exception as e:
                    if DEBUG:
                        print(f"Error: {e} in {fn}")
                    raise

            else:
                bo_seg = seg_pair
                en_seg = "\n"
            yield bo_post_process(bo_seg), en_seg

    text_bo_fn = tm_path / f"{tm_path.name}-bo.txt"
    text_en_fn = tm_path / f"{tm_path.name}-en.txt"

    with open(text_bo_fn, "w", encoding="utf-8") as bo_file, open(
        text_en_fn, "w", encoding="utf-8"
    ) as en_file:
        for bo_seg, en_seg in load_alignment(align_fn):
            bo_file.write(bo_seg + "\n")
            en_file.write(en_seg + "\n")

    return tm_path


def create_tm(align_fn: Path):
    align_fn = Path(align_fn)
    output_dir = align_fn.parent

    repo_name = get_github_repo_name()
    tm_path = output_dir / repo_name
    tm_path.mkdir(exist_ok=True, parents=True)
    tm_path = convert_raw_align_to_tm(align_fn, tm_path)
    repo_url = create_github_repo(tm_path, repo_name)
    print(f"[INFO] TM repo created: {repo_url}")
    return repo_url


if __name__ == "__main__":
    align_fn = Path(sys.argv[1])
    create_tm(align_fn)
