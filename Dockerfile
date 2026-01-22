# Image which will actually run the ImmuneBuilder app
#
# Build with
#    docker build -f Dockerfile.base -t immunebuilder:latest .

# Multi-stage Dockerfile for ImmuneBuilder app layers
ARG BASE_IMAGE=immunebuilder-base:latest
FROM ${BASE_IMAGE} AS builder
WORKDIR /app

# Copy package files (weights come from base image)
COPY pyproject.toml MANIFEST.in ./
COPY ImmuneBuilder/ ./ImmuneBuilder/
COPY data/ ./data/

# Install ImmuneBuilder from the repo in the existing conda env from base
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .


# ============================================
# CLI Stage - Minimal image for CLI tools
# ============================================
FROM builder as cli

# Verify installation
RUN TCRBuilder2 --help

# Set default command to show help
CMD ["TCRBuilder2", "--help"]
