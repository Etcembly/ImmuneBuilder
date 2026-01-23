# Development Setup Guide

## Prerequisites

ImmuneBuilder requires conda for dependency management, particularly for `pdbfixer` and `openmm` which only exist on `conda`.

First install Miniconda if you don't have it already:

```bash
# (Ganymede)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

If you're on `zsh`:

```bash
~/miniconda3/bin/conda init zsh
source ~/.zshrc
```

If you're just using `bash`:

```bash
source ~/.bashrc
```

Then check conda is avaliable:

```bash
conda --version  # Should show: conda 25.x.x
```

## Installation

Create conda environment:

```bash
# Create environment with Python 3.11
conda create -n immb python=3.11 -y
conda activate immb
```

Install various dependencies:

```bash
# Install libstdcxx-ng FIRST to avoid compatibility issues
conda install -c conda-forge libstdcxx-ng -y
# Now install openmm and pdbfixer
conda install -c conda-forge openmm pdbfixer -y
conda install -c bioconda anarci -y
```

Install ImmuneBuilder:

```bash
# Editable install with dev dependencies (recommended)
pip install -e ".[dev]"

# Or with all dependencies including API
pip install -e ".[all]"

# Or minimal install
pip install -e .
```

Test the build (without model weights)

```bash
# Test command-line tools
ABodyBuilder2 --help
TCRBuilder2 --help
NanoBodyBuilder2 --help
```

## Downloading models to use "locally"

To actually run the tool locally you will need the model weights:

- TCRBuilder2+ weights: https://zenodo.org/record/10892159
- Nanobody weights: https://zenodo.org/records/7258553

These need to be placed under `ImmuneBuilder/trained_model`, download via:

```bash
cd ImmuneBuilder/trained_model
curl -L -o tcr_model_1 "https://zenodo.org/record/10892159/files/tcr_model_1?download=1"
curl -L -o tcr_model_2 "https://zenodo.org/record/10892159/files/tcr_model_2?download=1"
curl -L -o tcr_model_3 "https://zenodo.org/record/10892159/files/tcr_model_3?download=1"
curl -L -o tcr_model_4 "https://zenodo.org/record/10892159/files/tcr_model_4?download=1"
curl -L -o nanobody_model_1 "https://zenodo.org/records/7258553/files/nanobody_model_1?download=1"
curl -L -o nanobody_model_2 "https://zenodo.org/records/7258553/files/nanobody_model_2?download=1"
curl -L -o nanobody_model_3 "https://zenodo.org/records/7258553/files/nanobody_model_3?download=1"
curl -L -o nanobody_model_4 "https://zenodo.org/records/7258553/files/nanobody_model_4?download=1"
```

## Running the tool on real data

```bash
echo ">B
ADVTQTPRNRITKTGKRIMLECSQTKGHDRMYWYRQDPGLGLRLIYYSFDVKDINKGEISDGYSVSRQAQAKFSLSLESAIPNQTALYFCATSDESYGYTFGSGTRLTVV
>A
AQSVTQLGSHVSVSEGALVLLRCNYSSSVPPYLFWYVQYPNQGLQLLLKYTSAATLVKGINGFEAEFKKSETSFHLTKPSAHMSDAAEYFCAVSEQDDKIIFGKGTRLHILP" > test.fasta

TCRBuilder2 -f test.fasta -o test_tcr.pdb -v
```

```bash
echo ">H
QVQLVESGGGLVQPGESLRLSCAASGSIFGIYAVHWFRMAPGKEREFTAGFGSHGSTNYAASVKGRFTMSRDNAKNTTYLQMNSLKPADTAVYYCHALIKNELGFLDYWGPGTQVTVSS" > test.fasta

NanoBodyBuilder2 -f test.fasta -o test_nanobody.pdb -v
```


## Docker builds

There are two separate Dockerfiles:

### 1. Build the base image (conda env + model weights)

`Dockerfile.base` creates a reusable base image with all system dependencies, conda environment, and pre-downloaded model weights.

Build and push to GCP Artifact Registry (NOT done in GitHub actions):

```bash
VERSION=1.0
docker build -t immunebuilder-base:${VERSION} -f Dockerfile.base .
docker tag immunebuilder-base:${VERSION} europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder-base:${VERSION}
docker push europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder-base:${VERSION}
```

### 2. Build the API image (uses base image)

`Dockerfile` builds from the base image and adds the FastAPI application.

Build locally:

```bash
# Use latest base image
docker build -t immunebuilder:latest .

# Or use a specific version
VERSION=1.0
docker build -t immunebuilder:${VERSION} --build-arg VERSION=${VERSION} .
```

Build and push to GCP Artifact Registry (done in GitHub Actions too eventually):

```bash
VERSION=1.0

# Build with latest tag and --build-arg for base image version
docker build \
  --build-arg VERSION=${VERSION} \
  -t europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder:latest \
  .

# Push both tags
docker push europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder:latest
docker push europe-west2-docker.pkg.dev/emly-copilot-ci/copilot/immunebuilder:${VERSION}
```


## Other dev stuff

Setup pre-commit hooks :angel:

```bash
pre-commit install
```
