"""Mock Ollama API responses for testing."""

from typing import Dict, List, Any


def get_mock_models_response() -> Dict[str, Any]:
    """Mock response for /api/tags endpoint."""
    return {
        "models": [
            {
                "name": "llama2:latest",
                "modified_at": "2024-01-01T00:00:00Z",
                "size": 3826793677,
                "digest": "abc123"
            },
            {
                "name": "mistral:latest",
                "modified_at": "2024-01-01T00:00:00Z",
                "size": 4109865159,
                "digest": "def456"
            },
            {
                "name": "granite3.3:8b",
                "modified_at": "2024-01-01T00:00:00Z",
                "size": 5000000000,
                "digest": "ghi789"
            }
        ]
    }


def get_mock_generate_response(text: str = "Test response") -> Dict[str, Any]:
    """Mock response for /api/generate endpoint."""
    return {
        "model": "llama2:latest",
        "created_at": "2024-01-01T00:00:00Z",
        "response": text,
        "done": True,
        "context": [1, 2, 3, 4, 5],
        "total_duration": 1000000000,
        "load_duration": 500000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000000,
        "eval_count": 20,
        "eval_duration": 300000000
    }


def get_mock_streaming_chunks(text: str = "Hello world") -> List[bytes]:
    """Mock streaming response chunks."""
    words = text.split()
    chunks = []
    for i, word in enumerate(words):
        chunk = {
            "model": "llama2:latest",
            "created_at": "2024-01-01T00:00:00Z",
            "response": word + (" " if i < len(words) - 1 else ""),
            "done": False
        }
        chunks.append(json.dumps(chunk).encode() + b'\n')

    # Final done chunk
    final_chunk = {
        "model": "llama2:latest",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "",
        "done": True
    }
    chunks.append(json.dumps(final_chunk).encode() + b'\n')
    return chunks


def get_mock_error_response() -> Dict[str, Any]:
    """Mock error response."""
    return {
        "error": "model not found"
    }


import json
