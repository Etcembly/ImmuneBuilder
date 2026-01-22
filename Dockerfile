########################################
# Base stage: conda env + model weights
# Build: docker build -t immunebuilder-base:latest --target base .
########################################
FROM continuumio/miniconda3:25.3.1-1 AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONDA_AUTO_UPDATE_CONDA=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download model weights
RUN mkdir -p /app/ImmuneBuilder/trained_model && \
    cd /app/ImmuneBuilder/trained_model && \
    curl -L --retry 3 --retry-delay 2 -o tcr_model_1 "https://zenodo.org/record/10892159/files/tcr_model_1?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o tcr_model_2 "https://zenodo.org/record/10892159/files/tcr_model_2?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o tcr_model_3 "https://zenodo.org/record/10892159/files/tcr_model_3?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o tcr_model_4 "https://zenodo.org/record/10892159/files/tcr_model_4?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o nanobody_model_1 "https://zenodo.org/record/7258553/files/nanobody_model_1?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o nanobody_model_2 "https://zenodo.org/record/7258553/files/nanobody_model_2?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o nanobody_model_3 "https://zenodo.org/record/7258553/files/nanobody_model_3?download=1" && \
    curl -L --retry 3 --retry-delay 2 -o nanobody_model_4 "https://zenodo.org/record/7258553/files/nanobody_model_4?download=1"

# # ALT: Copy model weights from the local repository into the base image
# COPY ImmuneBuilder/trained_model /app/ImmuneBuilder/trained_model

# Create conda environment and install dependencies
RUN conda create -n immunebuilder python=3.11 -y && \
    conda run -n immunebuilder conda install -c conda-forge libstdcxx-ng -y && \
    conda run -n immunebuilder conda install -c conda-forge openmm pdbfixer -y && \
    conda run -n immunebuilder conda install -c bioconda anarci -y && \
    conda run -n immunebuilder conda remove --force ncurses -y && \
    conda run -n immunebuilder pip install --no-cache-dir --upgrade pip setuptools wheel && \
    conda run -n immunebuilder pip install --no-cache-dir torch numpy scipy einops requests

# Environment variables
ENV PATH /opt/conda/envs/immunebuilder/bin:$PATH
ENV CONDA_DEFAULT_ENV immunebuilder
ENV LD_LIBRARY_PATH /opt/conda/envs/immunebuilder/lib:$LD_LIBRARY_PATH

########################################
# Builder stage: install ImmuneBuilder
# Build: docker build -t immunebuilder:builder --target builder .
########################################
FROM base AS builder
WORKDIR /app

# Copy package files (weights come from base image)
COPY pyproject.toml MANIFEST.in ./
COPY ImmuneBuilder/ ./ImmuneBuilder/
COPY data/ ./data/

# Install ImmuneBuilder from the repo in the existing conda env from base
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .


########################################
# CLI Stage - Minimal image for CLI tools
# Build: docker build -t immunebuilder:cli --target cli .
########################################
FROM builder as cli

# Verify installation
RUN TCRBuilder2 --help

# Set default command to show help
CMD ["TCRBuilder2", "--help"]
