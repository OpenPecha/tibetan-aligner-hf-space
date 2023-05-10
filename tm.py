import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict

import requests

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_EMAIL = os.getenv("GITHUB_EMAIL")
GITHUB_ORG = os.getenv("MAI_GITHUB_ORG")
GITHUB_API_ENDPOINT = f"https://api.github.com/orgs/{GITHUB_ORG}/repos"

DEBUG = os.getenv("DEBUG", False)

quiet = "-q" if DEBUG else ""


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
        GITHUB_API_ENDPOINT,
        json={
            "name": repo_name,
            "private": True,
        },
        auth=(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN),
    )
    response.raise_for_status()

    time.sleep(3)

    # Add the GitHub remote to the local Git repository and push the changes
    remote_url = f"https://{GITHUB_ORG}:{GITHUB_ACCESS_TOKEN}@github.com/MonlamAI/{repo_name}.git"
    subprocess.run(
        f"git remote add origin {remote_url}", cwd=str(repo_path), shell=True
    )
    # rename default branch to main
    subprocess.run("git branch -M main".split(), cwd=str(repo_path))
    subprocess.run(f"git push {quiet} -u origin main".split(), cwd=str(repo_path))

    return response.json()["html_url"]


def convert_raw_align_to_tm(align_fn: Path, tm_path: Path):
    if DEBUG:
        logging.debug("[INFO] Conerting raw alignment to TM repo...")

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
                    logging.error(f"{e} in {fn}")
                    raise

            else:
                bo_seg = seg_pair
                en_seg = "\n"
            yield bo_seg, en_seg

    text_bo_fn = tm_path / f"{tm_path.name}-bo.txt"
    text_en_fn = tm_path / f"{tm_path.name}-en.txt"

    with open(text_bo_fn, "w", encoding="utf-8") as bo_file, open(
        text_en_fn, "w", encoding="utf-8"
    ) as en_file:
        for bo_seg, en_seg in load_alignment(align_fn):
            bo_file.write(bo_seg + "\n")
            en_file.write(en_seg + "\n")

    return tm_path


def get_github_dev_url(raw_github_url: str) -> str:
    base_url = "https://github.dev"
    _, file_path = raw_github_url.split(".com")
    blob_file_path = file_path.replace("main", "blob/main")
    return base_url + blob_file_path


def add_input_in_readme(input_dict: Dict[str, str], path: Path) -> Path:
    input_readme_fn = path / "README.md"
    text_id = input_dict["text_id"]
    bo_file_url = get_github_dev_url(input_dict["bo_file_url"])
    en_file_url = get_github_dev_url(input_dict["en_file_url"])
    input_string = "## Input\n- [BO{}]({})\n- [EN{}]({})".format(
        text_id, bo_file_url, text_id, en_file_url
    )

    input_readme_fn.write_text(input_string)

    return path


def create_tm(align_fn: Path, text_pair: Dict[str, str]):
    align_fn = Path(align_fn)
    text_id = text_pair["text_id"]
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        repo_name = f"TM{text_id}"
        tm_path = output_dir / repo_name
        tm_path.mkdir(exist_ok=True, parents=True)
        repo_path = convert_raw_align_to_tm(align_fn, tm_path)
        repo_path = add_input_in_readme(text_pair, tm_path)
        repo_url = create_github_repo(repo_path, repo_name)
        logging.info(f"TM repo created: {repo_url}")
    return repo_url


if __name__ == "__main__":
    align_fn = Path(sys.argv[1])
    create_tm(align_fn)
