import logging
import os
import re
import shutil
import stat
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import gradio as gr
import requests

from tm import create_tm

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ALIGNER_SCRIPT_DIR = Path("./tibetan-aligner").resolve()
ALIGNER_SCRIPT_NAME = "align_tib_en.sh"
ALIGNER_SCRIPT_PATH = ALIGNER_SCRIPT_DIR / ALIGNER_SCRIPT_NAME
assert ALIGNER_SCRIPT_PATH.is_file()


def make_dir_executable(dir_path: Path):
    for fn in dir_path.iterdir():
        st = os.stat(fn)
        os.chmod(fn, st.st_mode | stat.S_IEXEC)
        st = os.stat(fn)
        os.chmod(fn, st.st_mode | stat.S_IXGRP)
        st = os.stat(fn)
        os.chmod(fn, st.st_mode | stat.S_IXOTH)


make_dir_executable(ALIGNER_SCRIPT_DIR)


@contextmanager
def TemporaryDirectory():
    tmpdir = Path("./output").resolve() / uuid.uuid4().hex[:8]
    tmpdir.mkdir(exist_ok=True, parents=True)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(str(tmpdir))


def download_file(github_file_url: str, output_fn) -> Path:
    """Download file from github"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    authenticated_file_url = f"{github_file_url}?token={GITHUB_TOKEN}"
    with requests.get(authenticated_file_url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(output_fn, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return output_fn


def _run_align_script(bo_fn, en_fn, output_dir):
    start = time.time()
    cmd = [str(ALIGNER_SCRIPT_PATH), str(bo_fn), str(en_fn), str(output_dir)]
    output = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ALIGNER_SCRIPT_DIR),
        shell=True,
    )
    output_fn = re.search(r"\[OUTPUT\] (.*)", output.stdout).group(1)
    output_fn = "/" + output_fn.split("//")[-1]
    end = time.time()
    total_time = round((end - start) / 60, 2)
    logging.info(f"Total time taken for Aligning: {total_time} mins")
    return output_fn


def align(text_pair):
    logging.info(f"Running aligner on MT{text_pair['text_id']}")
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        bo_fn = download_file(text_pair["bo_file_url"], output_fn=output_dir / "bo.tx")
        en_fn = download_file(text_pair["en_file_url"], output_fn=output_dir / "en.tx")
        aligned_fn = _run_align_script(bo_fn, en_fn, output_dir)
        repo_url = create_tm(aligned_fn, text_id=text_pair["text_id"])
        return {"tm_repo_url": repo_url}


with gr.Blocks() as demo:
    gr.Markdown("## Tibetan-English Aligner API")
    gr.Markdown("Please use Via API")
    input = gr.JSON(
        value={
            "text_id": f"{uuid.uuid4().hex[:4]}",
            "bo_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-bo.txt",
            "en_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-en.txt",
        }
    )
    output = gr.JSON()
    align_btn = gr.Button("Align")
    align_btn.click(
        fn=align,
        inputs=input,
        outputs=output,
        api_name="align",
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True, debug=True)
