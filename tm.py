import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

from github_utils import (
    clone_repo,
    commit_and_push,
    commit_to_orphan_branch,
    create_github_repo,
    get_branches,
    repo_exists,
)

DEBUG = os.getenv("DEBUG", False)


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


def tm_exists(tm_id):
    return repo_exists(tm_id)


def download_tm(tm_id: str, output_dir: Path):
    tm_path = clone_repo(tm_id, output_dir)
    return tm_path


def get_next_version(tm_id: str):
    branches = get_branches(tm_id)
    versions = [b for b in branches if b.startswith("v")]
    if not versions:
        return "v1"
    else:
        sorted_versions = sorted(versions)
        return f"v{int(sorted_versions[-1][1:]) + 1}"


def create_tm(align_fn: Path, text_pair: Dict[str, str]):
    align_fn = Path(align_fn)
    text_id = text_pair["text_id"]
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        tm_id = f"TM{text_id}"
        tm_path = output_dir / tm_id
        tm_path.mkdir(exist_ok=True, parents=True)
        tm_path = convert_raw_align_to_tm(align_fn, tm_path)
        tm_path = add_input_in_readme(text_pair, tm_path)
        if tm_exists(tm_id):
            cloned_output_dir = output_dir / "cloned"
            cloned_output_dir.mkdir(exist_ok=True, parents=True)
            tm_repo_path = download_tm(tm_id, cloned_output_dir)
            tm_url = commit_and_push(
                repo_path=tm_repo_path,
                branch="main",
                files_to_add=tm_path.iterdir(),
                commit_message=f"update alignment",
            )
            logging.info(f"Update alignment for {tm_id}")
        else:
            tm_url = create_github_repo(repo_path=tm_path, repo_name=tm_id)
            logging.info(f"New {tm_id} created")
    return tm_url


if __name__ == "__main__":
    align_fn = Path(sys.argv[1])
    create_tm(align_fn)
