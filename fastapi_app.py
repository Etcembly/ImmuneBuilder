"""
FastAPI wrapper for TCRBuilder2 and NanoBodyBuilder2
"""

import logging
import os
import tempfile
from functools import wraps

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ImmuneBuilder import NanoBodyBuilder2, TCRBuilder2
from ImmuneBuilder.util import sequence_dict_from_fasta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TCRBuilder2 and NanoBodyBuilder2 API",
    description="REST API for T-Cell Receptor and Nanobody structure prediction using TCRBuilder2 and NanoBodyBuilder2",
    version="1.0.0",
)

CHECK_STRAINED_BONDS = True
N_THREADS = -1


def handle_exceptions(func):
    """Catch HTTPException and log general exceptions as 500.

    Will wrap endpoint functions to provide consistent top-level error handling."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            ) from e

    return wrapper


async def _save_and_parse_fasta(fasta_file: UploadFile, temp_dir: str):
    """Save uploaded FASTA file and parse sequences."""
    fasta_path = os.path.join(temp_dir, "input.fasta")
    with open(fasta_path, "wb") as f:
        content = await fasta_file.read()
        f.write(content)

    try:
        sequences = sequence_dict_from_fasta(fasta_path)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse FASTA file: {str(e)}"
        ) from e

    return sequences


@app.get("/health")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "TCRBuilder2 and NanoBodyBuilder2 API",
    }


@app.post("/predict/tcr")
@handle_exceptions
async def predict_tcr_structure(
    fasta_file: UploadFile = File(
        ..., description="FASTA file with B and A chains for TCR"
    )
):
    """
    Predict TCR structure from a FASTA file containing beta (B) and alpha (A) chains.
    """
    temp_dir = tempfile.mkdtemp(prefix="tcrbuilder2_")
    sequences = await _save_and_parse_fasta(fasta_file, temp_dir)

    if "B" not in sequences or "A" not in sequences:
        raise HTTPException(
            status_code=400,
            detail="FASTA file must contain both beta chain (B) and alpha chain (A)",
        )

    logger.info(
        f"Loaded sequences - Beta: {len(sequences['B'])} aa, Alpha: {len(sequences['A'])} aa"
    )

    try:
        predicted_tcr = TCRBuilder2(use_TCRBuilder2_PLUS_weights=True).predict(
            sequences
        )
    except AssertionError as e:
        raise HTTPException(
            status_code=400, detail=f"Sequence validation failed: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}"
        ) from e

    output_filename = "tcr_structure.pdb"
    output_pdb = os.path.join(temp_dir, output_filename)
    predicted_tcr.save(
        filename=output_pdb,
        check_for_strained_bonds=CHECK_STRAINED_BONDS,
        n_threads=N_THREADS,
    )
    logger.info(f"Saved structure: {output_pdb}")

    return FileResponse(
        output_pdb, media_type="chemical/x-pdb", filename=output_filename
    )


@app.post("/predict/nanobody")
@handle_exceptions
async def predict_nanobody_structure(
    fasta_file: UploadFile = File(
        ..., description="FASTA file with a single nanobody chain"
    )
):
    """
    Predict nanobody structure from a FASTA file containing a single chain.
    """
    temp_dir = tempfile.mkdtemp(prefix="nanobody_")
    sequences = await _save_and_parse_fasta(fasta_file, temp_dir)

    if len(sequences) != 1:
        raise HTTPException(
            status_code=400,
            detail="FASTA file must contain exactly one nanobody chain",
        )

    try:
        predicted_nanobody = NanoBodyBuilder2().predict(sequences)
    except AssertionError as e:
        raise HTTPException(
            status_code=400, detail=f"Sequence validation failed: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}"
        ) from e

    output_filename = "nanobody_structure.pdb"
    output_pdb = os.path.join(temp_dir, output_filename)
    predicted_nanobody.save(
        filename=output_pdb,
        check_for_strained_bonds=CHECK_STRAINED_BONDS,
        n_threads=N_THREADS,
    )
    logger.info(f"Saved structure: {output_pdb}")

    return FileResponse(
        output_pdb, media_type="chemical/x-pdb", filename=output_filename
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
