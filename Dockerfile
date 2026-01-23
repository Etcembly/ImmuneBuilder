# This Dockerfile builds the ImmuneBuilder application image
# It uses the base image defined in Dockerfile.base

ARG VERSION=latest

FROM europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder-base:${VERSION}
WORKDIR /app

# Copy package files (weights come from base image)
COPY pyproject.toml MANIFEST.in ./
COPY ImmuneBuilder/*.py ./ImmuneBuilder/
COPY data/ ./data/
COPY fastapi_app.py ./

# Install ImmuneBuilder and API dependencies from the repo
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
