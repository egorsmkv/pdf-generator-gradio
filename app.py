import sys
import subprocess
from pathlib import Path
from os import getenv

from importlib.metadata import version
from PIL import Image
from minijinja import Environment

import gradio as gr

# Config
document_name = "document-template.typ"

do_share = getenv("DO_SHARE")

concurrency_limit = getenv("CONCURRENCY_LIMIT", 1)

typst_bin_path = getenv("TYPST_BIN", "/home/user/app/typst")

# App description
title = "Typst-based PDF generation"

examples = [
    """
I begin this story with a neutral statement.
Basically this is a very silly test.
""",
]

description_head = f"""
# {title}

## Overview

We use https://typst.app to generate a PDF file with some parameters from this Gradio app.
""".strip()

tech_env = f"""
#### Environment

- Python: {sys.version}
""".strip()


def app_version(bin_path):
    return subprocess.run([bin_path, "--version"], capture_output=True, text=True)


def typst_compile(typst_bin_path, filename, export_template):
    args = [typst_bin_path, "compile", filename, export_template]
    print("Running:", args)

    return subprocess.run(
        args,
        capture_output=False,
    )


def convert_document(bin_paths, text):
    print("Converting...")

    env = Environment(
        templates={
            "document": Path("document-template.typ").read_text(),
        }
    )
    formatted_document = env.render_template("document", text=text)

    # Write the rendered document to a temporary file
    document_file = Path("document.typ")
    document_file.write_text(formatted_document)

    # Compile the .typ file to a .pdf file
    c = typst_compile(bin_paths["typst"], "document.typ", "document.pdf")
    if c.returncode != 0:
        raise gr.Error("Typst compilation failed.")

    print("Result:", c)

    # Extract the first page of the PDF file
    c = typst_compile(bin_paths["typst"], "document.typ", "file-{n}.png")
    if c.returncode != 0:
        raise gr.Error("Typst exporting to PNGs failed.")

    print("Result:", c)

    first_page = Path("file-1.png")
    if not first_page.exists():
        raise gr.Error("The first page has not been exported.")

    # Move the image to an object
    image = Image.open(first_page.absolute())

    # Remove the temporary files
    first_page.unlink(missing_ok=True)
    document_file.unlink(missing_ok=True)

    return image


typst_version_info = app_version(typst_bin_path)
if typst_version_info.returncode != 0:
    print("Error: Typst version command failed.")
    exit(1)

r_tech_env = f"""
#### Typst Environment

```
{typst_version_info.stdout.strip()}
```
""".strip()

tech_libraries = f"""
#### Libraries

- gradio: {version("gradio")}
""".strip()


def generate_pdf(text, progress=gr.Progress()):
    if not text:
        raise gr.Error("Please paste your text.")

    # Remove the previous PDF file and Typst file
    Path("document.pdf").unlink(missing_ok=True)
    Path("document.typ").unlink(missing_ok=True)

    gr.Info("Generating the PDF document", duration=1)

    bin_paths = {
        "typst": typst_bin_path,
    }
    image = convert_document(bin_paths, text)

    gr.Success("Finished!", duration=2)

    pdf_file = gr.DownloadButton(
        label="Download document.pdf",
        value="./document.pdf",
        visible=True,
    )

    return [image, pdf_file]


demo = gr.Blocks(
    title=title,
    analytics_enabled=False,
    theme=gr.themes.Base(),
)

with demo:
    gr.Markdown(description_head)

    gr.Markdown("## Usage")

    with gr.Row():
        text = gr.Textbox(label="Text", autofocus=True, max_lines=50)

        with gr.Column():
            pdf_file = gr.DownloadButton(label="Download PDF", visible=False)
            preview_image = gr.Image(
                label="Preview image",
            )

    gr.Button("Generate").click(
        generate_pdf,
        concurrency_limit=concurrency_limit,
        inputs=text,
        outputs=[preview_image, pdf_file],
    )

    with gr.Row():
        gr.Examples(label="Choose an example", inputs=text, examples=examples)

    gr.Markdown("### Gradio app uses:")
    gr.Markdown(tech_env)
    gr.Markdown(r_tech_env)
    gr.Markdown(tech_libraries)

if __name__ == "__main__":
    demo.queue()

    if do_share:
        demo.launch(share=True)
    else:
        demo.launch()
