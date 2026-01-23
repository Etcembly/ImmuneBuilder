# This Dockerfile builds the ImmuneBuilder application image
# It uses the base image defined in Dockerfile.base

ARG VERSION=latest

FROM europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder-base:${VERSION}
WORKDIR /app

# Copy package files (weights come from base image)
COPY pyproject.toml MANIFEST.in ./
COPY ImmuneBuilder/ ./ImmuneBuilder/
COPY data/ ./data/

# Install ImmuneBuilder and API dependencies from the repo
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e '.[all]'

# Verify installation - this will eventually be an API endpoint
RUN TCRBuilder2 --help

# Set default command to show help
CMD ["TCRBuilder2", "--help"]
