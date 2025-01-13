# Generate PDF documents using Gradio and Typst

- minijinja to template a Typst document
- Typst to generate a PDF document
- Gradio to provide a web interface with user parameters (via Components)
- Docker to run the app

## Demo

<img src="./demo.jpeg" width="800">

## Install

Clone the repository:

```bash
git clone https://github.com/egorsmkv/pdf-generator-gradio
cd pdf-generator-gradio
```

Install `typst`:

```bash
cargo install typst-cli
```

## Development

Create virtual environment and install dependencies:

```bash
uv venv --python 3.13

source .venv/bin/activate

uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

## Run

Run Gradio app locally:

```bash
export TYPST_BIN=/home/yehor/.cargo/bin/typst

gradio app.py
```

## Production

Build the Docker image:

```bash
docker build -t pdf-generator-gradio .
```

Run:

```bash
docker run --rm -p 7860:7860 -it pdf-generator-gradio

# Enable Gradio sharing
docker run --rm -p 7860:7860 -e DO_SHARE=y -it pdf-generator-gradio
```
