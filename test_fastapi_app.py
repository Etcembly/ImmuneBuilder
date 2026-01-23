"""
Unit tests for fastapi_app.py helper functions
"""

import os
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

# Mock heavy dependencies before importing ImmuneBuilder
sys.modules["pdbfixer"] = MagicMock()
sys.modules["openmm"] = MagicMock()
sys.modules["openmm.app"] = MagicMock()
sys.modules["openmm.unit"] = MagicMock()

from fastapi_app import _save_and_parse_fasta, handle_exceptions  # noqa: E402


class TestHandleExceptions:
    """Test the handle_exceptions decorator"""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Decorator should pass through successful results"""

        @handle_exceptions
        async def successful_func():
            return {"status": "ok"}

        result = await successful_func()
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_reraises_http_exception(self):
        """Decorator should re-raise HTTPException without modification"""

        @handle_exceptions
        async def raises_http_exception():
            raise HTTPException(status_code=400, detail="Bad request")

        with pytest.raises(HTTPException) as exc_info:
            await raises_http_exception()

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad request"

    @pytest.mark.asyncio
    async def test_converts_general_exception_to_500(self):
        """Decorator should convert general exceptions to 500 HTTPException"""

        @handle_exceptions
        async def raises_general_exception():
            raise ValueError("Something went wrong")

        with pytest.raises(HTTPException) as exc_info:
            await raises_general_exception()

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail
        assert "Something went wrong" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exception_chaining(self):
        """Decorator should preserve exception chaining"""

        @handle_exceptions
        async def raises_chained_exception():
            raise RuntimeError("Original error")

        with pytest.raises(HTTPException) as exc_info:
            await raises_chained_exception()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert str(exc_info.value.__cause__) == "Original error"


class TestSaveAndParseFasta:
    """Test the _save_and_parse_fasta helper function"""

    @pytest.mark.asyncio
    async def test_successful_fasta_parsing(self):
        """Should successfully save and parse valid FASTA file"""
        # Mock UploadFile
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b">seq1\nACGT\n>seq2\nTGCA\n")

        # Mock sequence_dict_from_fasta
        expected_sequences = {"seq1": "ACGT", "seq2": "TGCA"}

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("fastapi_app.sequence_dict_from_fasta") as mock_parser:
                mock_parser.return_value = expected_sequences

                result = await _save_and_parse_fasta(mock_file, temp_dir)

                # Verify file was written
                fasta_path = os.path.join(temp_dir, "input.fasta")
                assert os.path.exists(fasta_path)

                # Verify parser was called with correct path
                mock_parser.assert_called_once_with(fasta_path)

                # Verify result
                assert result == expected_sequences

    @pytest.mark.asyncio
    async def test_writes_file_content_correctly(self):
        """Should write uploaded file content to disk"""
        fasta_content = b">TestSeq\nMKLLILAVVLSVLLGAQG\n"
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=fasta_content)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("fastapi_app.sequence_dict_from_fasta") as mock_parser:
                mock_parser.return_value = {"TestSeq": "MKLLILAVVLSVLLGAQG"}

                await _save_and_parse_fasta(mock_file, temp_dir)

                # Verify file content & that file was created
                fasta_path = os.path.join(temp_dir, "input.fasta")
                assert os.path.exists(fasta_path)
                assert os.path.isfile(fasta_path)
                with open(fasta_path, "rb") as f:
                    content = f.read()
                assert content == fasta_content

    @pytest.mark.asyncio
    async def test_raises_http_exception_on_parse_failure(self):
        """Should raise HTTPException when FASTA parsing fails"""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"invalid fasta content")

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("fastapi_app.sequence_dict_from_fasta") as mock_parser:
                mock_parser.side_effect = ValueError("Invalid FASTA format")

                with pytest.raises(HTTPException) as exc_info:
                    await _save_and_parse_fasta(mock_file, temp_dir)

                assert exc_info.value.status_code == 400
                assert "Failed to parse FASTA file" in exc_info.value.detail
                assert "Invalid FASTA format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_preserves_exception_chain_on_parse_failure(self):
        """Should preserve exception chaining when parsing fails"""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"bad data")

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("fastapi_app.sequence_dict_from_fasta") as mock_parser:
                original_error = RuntimeError("Parser crashed")
                mock_parser.side_effect = original_error

                with pytest.raises(HTTPException) as exc_info:
                    await _save_and_parse_fasta(mock_file, temp_dir)

                assert exc_info.value.__cause__ == original_error
