import gradio as gr
import requests



def align():
    return {"success": True}


def run():
    demo = gr.Interface(
        fn=align,
        inputs=gr.inputs.JSON(
            value={
                "bo_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-bo.txt",
                "en_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-en.txt"
            }
        ),
        outputs=gr.outputs.JSON(),
    )

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    run()
