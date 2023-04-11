import os
import re
import subprocess
import tempfile
from pathlib import Path

import gradio as gr
import requests

DEV = os.environ.get("DEV", False)


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
    aligner_script_dir = "../tibetan-aligner"
    cmd = ["../tibetan-aligner/align_tib_en.sh", bo_fn, en_fn, output_dir]
    output = subprocess.run(
        cmd, check=True, capture_output=True, text=True, cwd=aligner_script_dir
    )
    output_fn = re.search(r"\[OUTPUT\] (.*)", output.stdout).group(1)
    output_fn = "/" + output_fn.split("//")[-1]
    return output_fn


def align(file_urls):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        bo_fn = download_file(file_urls["bo_file_url"], output_dir)
        en_fn = download_file(file_urls["en_file_url"], output_dir)
        aligned_fn = _run_align_script(bo_fn, en_fn, output_dir)
        return Path(aligned_fn).read_text()


if DEV:
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
else:
    demo = gr.Interface(
        fn=align,
        inputs=gr.JSON(
            value={
                "bo_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-bo.txt",
                "en_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-en.txt",
            }
        ),
        outputs=gr.TextArea(),
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True, debug=True)
