FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    # python build dependencies \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # gradio dependencies \
    ffmpeg imagemagick ghostscript

RUN apt install -y --reinstall ca-certificates && update-ca-certificates -f

COPY --chown=1000 ./policy.xml /tmp/policy.xml
RUN rm /etc/ImageMagick-6/policy.xml && mv /tmp/policy.xml /etc/ImageMagick-6/policy.xml

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:${PATH}
ENV MAGICK_CONFIGURE_PATH=${HOME}/app
WORKDIR ${HOME}/app

RUN wget "https://github.com/typst/typst/releases/download/v0.11.1/typst-x86_64-unknown-linux-musl.tar.xz" && \
    tar -xf typst-x86_64-unknown-linux-musl.tar.xz && \
    mv typst-x86_64-unknown-linux-musl/typst . && \
    rm -rf typst-x86_64-unknown-linux-musl && \
    rm typst-x86_64-unknown-linux-musl.tar.xz

RUN curl https://pyenv.run | bash

ENV PATH=${HOME}/.pyenv/shims:${HOME}/.pyenv/bin:${PATH}

ARG PYTHON_VERSION=3.12.5
RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash && \
    pip install --no-cache-dir -U pip setuptools wheel && \
    pip install packaging ninja

COPY --chown=1000 ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

COPY --chown=1000 . ${HOME}/app
ENV PYTHONPATH=${HOME}/app \
    PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces

EXPOSE 7860

CMD ["python", "app.py"]
