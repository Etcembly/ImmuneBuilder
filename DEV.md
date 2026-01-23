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

## Running the FastAPI server locally

FastAPI app lives in `fastapi_app.py`.

Run locally with auto-reload:

```bash
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:
- Health: http://localhost:8000/health
- Docs (Swagger): http://localhost:8000/docs
- TCR prediction: POST http://localhost:8000/predict/tcr (form field `fasta_file`)
- Nanobody prediction: POST http://localhost:8000/predict/nanobody (form field `fasta_file`)

Example curl:

```bash
curl -X POST "http://localhost:8000/predict/tcr" \
	-F "fasta_file=@example_data/tcr.fasta" \
	-o tcr_structure.pdb
```


## Docker builds (multi-stage)

The single Dockerfile has multiple targets:

- `base`: builds the conda env (Python 3.11), installs deps, and downloads weights.
- `builder`: installs ImmuneBuilder into the env from `base`.
- `cli`: verifies CLI installation; default cmd shows TCRBuilder2 help (this will eventually be API endpoint)

Build examples:

```bash
# Base with weights baked in
docker build -t immunebuilder-base:latest --target base .

# App builder
docker build -t immunebuilder-builder:latest --target builder .

# CLI image
docker build -t immunebuilder-api:latest --target api .
```

If you prefer to copy local weights instead of downloading during build, uncomment the `COPY ImmuneBuilder/trained_model ...` line in the `base` stage and ensure `.dockerignore` does not exclude that path.


## Hitting the docker build

Run the API container:

```bash
docker run -p 8000:8000 immunebuilder-api:latest
```

Then:

```bash
# Health check
curl http://localhost:8000/health

# Swagger docs
open http://localhost:8000/docs

# TCR prediction
curl -X POST "http://localhost:8000/predict/tcr" \
  -F "fasta_file=@example_data/tcr.fasta" \
  -o tcr_structure.pdb

# Nanobody prediction
curl -X POST "http://localhost:8000/predict/nanobody" \
  -F "fasta_file=@example_data/nanobody.fasta" \
  -o nanobody_structure.pdb
```

## Other dev stuff

Setup pre-commit hooks :angel:

```bash
pre-commit install
```
