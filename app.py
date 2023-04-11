import os
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

import gradio as gr
import requests

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


def download_file(url, output_path=Path("./data")):
    output_path.mkdir(parents=True, exist_ok=True)
    local_filename = output_path / url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


def _run_align_script(bo_fn, en_fn, output_dir):
    cmd = [str(ALIGNER_SCRIPT_PATH), str(bo_fn), str(en_fn), str(output_dir)]
    print(cmd)
    output = subprocess.run(
        cmd, check=True, capture_output=True, text=True, cwd=str(ALIGNER_SCRIPT_DIR)
    )
    output_fn = re.search(r"\[OUTPUT\] (.*)", output.stdout).group(1)
    output_fn = "/" + output_fn.split("//")[-1]
    return output_fn


def align(file_urls):
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        bo_fn = download_file(file_urls["bo_file_url"], output_dir)
        en_fn = download_file(file_urls["en_file_url"], output_dir)
        aligned_fn = _run_align_script(bo_fn, en_fn, output_dir)
        return Path(aligned_fn).read_text()


with gr.Blocks() as demo:
    input = gr.JSON(
        value={
            "bo_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-bo.txt",
            "en_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-en.txt",
        }
    )
    output = gr.TextArea()
    align_btn = gr.Button("Align")
    align_btn.click(
        fn=align,
        inputs=input,
        outputs=output,
        api_name="align",
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True, debug=True)
