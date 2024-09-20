import sys
import subprocess
from os import remove
from os.path import exists

from importlib.metadata import version
from PIL import Image
from jinja2 import Environment, PackageLoader, select_autoescape

import gradio as gr


env = Environment(loader=PackageLoader("ui"), autoescape=select_autoescape())
template = env.get_template("typst_template.typ")


def app_version(bin_path):
    return subprocess.run([bin_path, "--version"], capture_output=True, text=True)


def typst_compile(typst_bin_path, filename):
    return subprocess.run(
        [typst_bin_path, "compile", filename],
        capture_output=False,
    )


def convert_document(bin_paths, text):
    print("Converting...")

    document = template.render(text=text)

    # Write the document to a .typ file
    with open("document.typ", "w") as f:
        f.write(document)

    # Compile the .typ file to a .pdf file
    c = typst_compile(bin_paths["typst"], "document.typ")
    if c.returncode != 0:
        raise gr.Error("Typst compilation failed.")

    print(c)

    # Extract the first page of the PDF file
    cmd = [
        bin_paths["imagemagic"],
        "document.pdf[0]",
        "-fuzz",
        "25%",
        "-fill",
        "white",
        "-opaque",
        "white",
        "-flatten",
        "first_page.png",
    ]
    print(" ".join(cmd))
    c = subprocess.run(
        cmd,
    )

    if c.returncode != 0:
        raise gr.Error("Failed to extract the first page of the PDF file.")

    # Move the image to an object
    image = Image.open("first_page.png")

    # Remove the temporary files
    remove("first_page.png")

    return image


# Config
concurrency_limit = 5

typst_bin_path = "/home/user/app/typst"
imagemagic_bin_path = "/usr/bin/convert"

examples = [
    """I begin this story with a neutral statement.  
Basically this is a very silly test.  
""",
]

title = "Typst-based PDF generation"

# https://www.tablesgenerator.com/markdown_tables
authors_table = """
## Authors

Follow them on social networks and **contact** if you need any help or have any questions:

| <img src="https://avatars.githubusercontent.com/u/7875085?v=4" width="100"> **Yehor Smoliakov** |
|-------------------------------------------------------------------------------------------------|
| https://t.me/smlkw in Telegram                                                                  |
| https://x.com/yehor_smoliakov at X                                                              |
| https://github.com/egorsmkv at GitHub                                                           |
| https://huggingface.co/Yehor at Hugging Face                                                    |
| or use egorsmkv@gmail.com                                                                       |
""".strip()

description_head = f"""
# {title}

## Overview

We use https://typst.app to generate a PDF file with some parameters from this Gradio app.
""".strip()

description_foot = f"""
{authors_table}
""".strip()

tech_env = f"""
#### Environment

- Python: {sys.version}
""".strip()

imagemagick_version_info = app_version(imagemagic_bin_path)
if imagemagick_version_info.returncode != 0:
    print("Error: ImageMagick version command failed.")
    exit(1)

typst_version_info = app_version(typst_bin_path)
if typst_version_info.returncode != 0:
    print("Error: Typst version command failed.")
    exit(1)
r_tech_env = f"""
#### Typst Environment

```
{typst_version_info.stdout.strip()}
```

#### ImageMagick Environment

```
{imagemagick_version_info.stdout.strip()}
```
""".strip()

tech_libraries = f"""
#### Libraries

- gradio: {version('gradio')}
""".strip()


def generate_pdf(text, progress=gr.Progress()):
    if not text:
        raise gr.Error("Please paste your text.")

    # Remove the previous PDF file and Typst file
    if exists("document.pdf"):
        remove("document.pdf")
    if exists("document.typ"):
        remove("document.typ")

    gr.Info("Generating the PDF document", duration=1)

    bin_paths = {
        "typst": typst_bin_path,
        "imagemagic": imagemagic_bin_path,
    }
    image = convert_document(bin_paths, text)

    gr.Info("Finished!", duration=2)

    pdf_file = gr.DownloadButton(
        label="Download document.pdf",
        value="./document.pdf",
        visible=True,
    )

    if exists("document.typ"):
        remove("document.typ")

    return [image, pdf_file]


demo = gr.Blocks(
    title=title,
    analytics_enabled=False,
    # theme="huggingface",
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

    gr.Markdown(description_foot)

    gr.Markdown("### Gradio app uses:")
    gr.Markdown(tech_env)
    gr.Markdown(r_tech_env)
    gr.Markdown(tech_libraries)

if __name__ == "__main__":
    demo.queue()
    demo.launch()
