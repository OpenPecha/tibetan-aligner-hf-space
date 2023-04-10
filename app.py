import tempfile
from pathlib import Path

import gradio as gr
import requests


def download_file(url, output_path=Path("./data")):
    output_path.mkdir(parents=True, exist_ok=True)
    local_filename = output_path / url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


def align(file_urls):
    with tempfile.TemporaryDirectory() as tmpdir:
        bo_fn = download_file(file_urls["bo_file_url"], Path(tmpdir))
        en_fn = download_file(file_urls["en_file_url"], Path(tmpdir))
    return bo_fn, en_fn


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
    demo.launch(server_name="0.0.0.0", server_port=7860)
