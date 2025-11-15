# API Integration Guide

Guide for integrating alternative LLM backends beyond the default Ollama setup.

## Table of Contents

- [Overview](#overview)
- [Supported Backends](#supported-backends)
- [OpenAI Integration](#openai-integration)
- [Anthropic Claude Integration](#anthropic-claude-integration)
- [Google Gemini Integration](#google-gemini-integration)
- [Azure OpenAI Integration](#azure-openai-integration)
- [Custom Backend Integration](#custom-backend-integration)
- [Cost Estimation](#cost-estimation)
- [Performance Comparison](#performance-comparison)
- [Migration Guide](#migration-guide)

---

## Overview

While Infinite AI Backrooms is designed to work with local Ollama models, it can be extended to support various cloud-based LLM APIs. This guide shows how to integrate alternative backends.

### Why Use Alternative Backends?

**Cloud APIs (OpenAI, Anthropic, etc.)**
- No local GPU requirements
- Access to latest models
- Managed infrastructure
- Pay-per-use pricing

**Local Ollama**
- Privacy and data control
- No per-request costs
- Offline capability
- Customizable models

---

## Supported Backends

| Provider | Status | Models | Pricing | Best For |
|----------|--------|--------|---------|----------|
| Ollama | ✅ Default | All Ollama models | Free (local) | Privacy, cost control |
| OpenAI | 🔧 Community | GPT-4, GPT-3.5 | $0.002-0.06/1K tokens | Quality, reliability |
| Anthropic | 🔧 Community | Claude 3.5 Sonnet | $0.003-0.015/1K tokens | Reasoning, context |
| Google | 🔧 Community | Gemini Pro | $0.0005-0.002/1K tokens | Cost-effective |
| Azure OpenAI | 🔧 Community | GPT-4 | Enterprise pricing | Enterprise, compliance |
| Hugging Face | 🔧 Community | Various | Free tier available | Experimentation |

**Legend:**
- ✅ Default: Built-in support
- 🔧 Community: Requires custom implementation

---

## OpenAI Integration

### Prerequisites

1. OpenAI API key from https://platform.openai.com/api-keys
2. Account with credits or payment method

### Implementation

#### Step 1: Install OpenAI SDK

```bash
uv pip install openai>=1.0.0
```

#### Step 2: Create OpenAI Client

Create `src/services/openai_client.py`:

```python
"""
OpenAI API client for Infinite Backrooms.
Drop-in replacement for OllamaClient.
"""
import os
from typing import AsyncGenerator, List, Dict
import openai
from openai import AsyncOpenAI

class OpenAIClient:
    """OpenAI API client compatible with Ollama interface."""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        organization: str = None
    ):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORGANIZATION")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization,
            base_url=base_url
        )

    async def test_connection(self) -> tuple[bool, List[str]]:
        """Test connection and list available models."""
        try:
            models = await self.client.models.list()
            model_names = [
                model.id for model in models.data
                if model.id.startswith(("gpt-", "text-"))
            ]
            return True, model_names
        except Exception as e:
            return False, [str(e)]

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Generate streaming response from OpenAI API.

        Compatible with Ollama interface - yields dicts with 'type' and 'content'.
        """
        try:
            # Build messages list
            messages = []

            # System prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Context (conversation history)
            if context:
                messages.extend(context)

            # Current prompt
            messages.append({"role": "user", "content": prompt})

            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            # Stream response chunks
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield {
                            "type": "content",
                            "content": delta.content
                        }

            # Signal completion
            yield {"type": "done", "content": ""}

        except openai.APIError as e:
            yield {
                "type": "error",
                "content": f"OpenAI API error: {str(e)}"
            }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Error: {str(e)}"
            }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.close()
```

#### Step 3: Configure Environment

Add to `.env`:

```env
# Choose backend: ollama or openai
LLM_BACKEND=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_ORGANIZATION=org-your-org-id  # Optional

# Model mapping (OpenAI model names)
DEFAULT_MODEL=gpt-4-turbo-preview
FAST_MODEL=gpt-3.5-turbo
QUALITY_MODEL=gpt-4
```

#### Step 4: Update Main Application

Modify `streamlit_backroom.py`:

```python
import os
from src.services.ollama_client import OllamaClient
from src.services.openai_client import OpenAIClient

# Determine backend
BACKEND = os.getenv("LLM_BACKEND", "ollama")

def get_llm_client():
    """Get appropriate LLM client based on backend configuration."""
    if BACKEND == "openai":
        return OpenAIClient()
    elif BACKEND == "ollama":
        return OllamaClient(base_url=os.getenv("OLLAMA_URL"))
    else:
        raise ValueError(f"Unknown backend: {BACKEND}")

# Usage
async def generate_response(persona, prompt, context):
    async with get_llm_client() as client:
        async for chunk in client.generate_stream(
            model=persona.model,
            prompt=prompt,
            context=context,
            system_prompt=persona.system_prompt
        ):
            yield chunk
```

### OpenAI Model Selection

| Model | Speed | Quality | Cost ($/1M tokens) | Context Window | Best For |
|-------|-------|---------|-------------------|----------------|----------|
| gpt-4-turbo | Medium | Excellent | $10-30 | 128K | Production quality |
| gpt-4 | Slow | Excellent | $30-60 | 8K | Complex reasoning |
| gpt-3.5-turbo | Fast | Good | $0.5-1.5 | 16K | Fast interactions |
| gpt-3.5-turbo-16k | Fast | Good | $3-4 | 16K | Long context |

### Cost Management

```python
# Add token counting for cost tracking
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for cost estimation."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Log costs
def log_api_cost(prompt: str, response: str, model: str):
    """Calculate and log API costs."""
    prompt_tokens = count_tokens(prompt, model)
    response_tokens = count_tokens(response, model)

    # Pricing (example for GPT-4)
    if model.startswith("gpt-4"):
        prompt_cost = prompt_tokens * 0.00003  # $0.03/1K
        response_cost = response_tokens * 0.00006  # $0.06/1K
    elif model.startswith("gpt-3.5"):
        prompt_cost = prompt_tokens * 0.0000015  # $0.0015/1K
        response_cost = response_tokens * 0.000002  # $0.002/1K
    else:
        prompt_cost = response_cost = 0

    total_cost = prompt_cost + response_cost

    print(f"API Cost: ${total_cost:.4f} (Prompt: {prompt_tokens}, Response: {response_tokens})")
```

---

## Anthropic Claude Integration

### Prerequisites

1. Anthropic API key from https://console.anthropic.com/
2. Account with credits

### Implementation

#### Step 1: Install Anthropic SDK

```bash
uv pip install anthropic>=0.18.0
```

#### Step 2: Create Anthropic Client

Create `src/services/anthropic_client.py`:

```python
"""
Anthropic Claude API client for Infinite Backrooms.
"""
import os
from typing import AsyncGenerator, List, Dict
from anthropic import AsyncAnthropic

class AnthropicClient:
    """Anthropic Claude API client compatible with Ollama interface."""

    def __init__(self, api_key: str = None):
        """Initialize Anthropic client."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def test_connection(self) -> tuple[bool, List[str]]:
        """Test connection and list available models."""
        try:
            # Anthropic doesn't have a models list endpoint
            # Return known models
            models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            return True, models
        except Exception as e:
            return False, [str(e)]

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Generate streaming response from Claude API."""
        try:
            # Build messages list
            messages = []

            # Context (conversation history)
            if context:
                for msg in context:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Current prompt
            messages.append({"role": "user", "content": prompt})

            # Create streaming completion
            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield {
                        "type": "content",
                        "content": text
                    }

            # Signal completion
            yield {"type": "done", "content": ""}

        except Exception as e:
            yield {
                "type": "error",
                "content": f"Anthropic API error: {str(e)}"
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()
```

#### Step 3: Configure Environment

```env
# Use Anthropic backend
LLM_BACKEND=anthropic

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Model selection
DEFAULT_MODEL=claude-3-5-sonnet-20241022
FAST_MODEL=claude-3-haiku-20240307
QUALITY_MODEL=claude-3-opus-20240229
```

### Claude Model Selection

| Model | Speed | Quality | Cost ($/1M tokens) | Context Window | Best For |
|-------|-------|---------|-------------------|----------------|----------|
| Claude 3.5 Sonnet | Fast | Excellent | $3-15 | 200K | Best balance |
| Claude 3 Opus | Medium | Outstanding | $15-75 | 200K | Highest quality |
| Claude 3 Sonnet | Fast | Very Good | $3-15 | 200K | Cost-effective |
| Claude 3 Haiku | Very Fast | Good | $0.25-1.25 | 200K | High volume |

---

## Google Gemini Integration

### Prerequisites

1. Google Cloud project with Gemini API enabled
2. API key from https://makersuite.google.com/app/apikey

### Implementation

#### Step 1: Install Google SDK

```bash
uv pip install google-generativeai>=0.3.0
```

#### Step 2: Create Gemini Client

Create `src/services/gemini_client.py`:

```python
"""
Google Gemini API client for Infinite Backrooms.
"""
import os
from typing import AsyncGenerator, List, Dict
import google.generativeai as genai

class GeminiClient:
    """Google Gemini API client compatible with Ollama interface."""

    def __init__(self, api_key: str = None):
        """Initialize Gemini client."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")

        genai.configure(api_key=self.api_key)

    async def test_connection(self) -> tuple[bool, List[str]]:
        """Test connection and list available models."""
        try:
            models = [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro"
            ]
            return True, models
        except Exception as e:
            return False, [str(e)]

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Generate streaming response from Gemini API."""
        try:
            # Initialize model
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

            # Build prompt with context
            full_prompt = ""
            if system_prompt:
                full_prompt += f"{system_prompt}\n\n"

            if context:
                for msg in context:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    full_prompt += f"{role}: {msg['content']}\n"

            full_prompt += f"User: {prompt}\nAssistant:"

            # Generate streaming response
            response = gemini_model.generate_content(
                full_prompt,
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield {
                        "type": "content",
                        "content": chunk.text
                    }

            yield {"type": "done", "content": ""}

        except Exception as e:
            yield {
                "type": "error",
                "content": f"Gemini API error: {str(e)}"
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
```

#### Step 3: Configure Environment

```env
LLM_BACKEND=gemini
GOOGLE_API_KEY=your-api-key-here
DEFAULT_MODEL=gemini-1.5-flash
```

---

## Azure OpenAI Integration

For enterprise deployments with compliance requirements.

### Implementation

Create `src/services/azure_openai_client.py`:

```python
"""
Azure OpenAI API client for Infinite Backrooms.
"""
import os
from typing import AsyncGenerator, List, Dict
from openai import AsyncAzureOpenAI

class AzureOpenAIClient:
    """Azure OpenAI API client."""

    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        api_version: str = "2024-02-15-preview"
    ):
        """Initialize Azure OpenAI client."""
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version

        if not self.api_key or not self.endpoint:
            raise ValueError("Azure OpenAI credentials required")

        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )

    async def generate_stream(
        self,
        model: str,  # Azure deployment name
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Generate streaming response from Azure OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": prompt})

            stream = await self.client.chat.completions.create(
                model=model,  # Your Azure deployment name
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield {"type": "content", "content": delta.content}

            yield {"type": "done", "content": ""}

        except Exception as e:
            yield {"type": "error", "content": f"Azure OpenAI error: {str(e)}"}
```

Configuration:

```env
LLM_BACKEND=azure_openai
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=your-deployment-name  # Azure deployment name, not model name
```

---

## Custom Backend Integration

### Abstract Base Class

Create `src/services/base_client.py`:

```python
"""
Base class for LLM clients.
All backends must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def test_connection(self) -> tuple[bool, List[str]]:
        """
        Test connection and list available models.

        Returns:
            Tuple of (success: bool, models: List[str])
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Generate streaming response.

        Yields:
            Dict with 'type' and 'content' keys:
            - {"type": "content", "content": "text"}
            - {"type": "done", "content": ""}
            - {"type": "error", "content": "error message"}
        """
        pass

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
```

### Example: Hugging Face Integration

```python
"""
Hugging Face Inference API client.
"""
from src.services.base_client import BaseLLMClient
import aiohttp

class HuggingFaceClient(BaseLLMClient):
    """Hugging Face Inference API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Generate response from Hugging Face API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{model}"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                # Build full prompt
                full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
                if context:
                    for msg in context:
                        full_prompt += f"{msg['content']}\n"
                full_prompt += prompt

                payload = {
                    "inputs": full_prompt,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": max_tokens
                    }
                }

                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        yield {"type": "content", "content": data[0]["generated_text"]}
                        yield {"type": "done", "content": ""}
                    else:
                        yield {"type": "error", "content": await resp.text()}

        except Exception as e:
            yield {"type": "error", "content": str(e)}

    # Implement other abstract methods...
```

---

## Cost Estimation

### Monthly Cost Calculator

```python
def estimate_monthly_cost(
    messages_per_day: int,
    avg_message_length: int,
    personas: int,
    model: str
):
    """
    Estimate monthly API costs.

    Args:
        messages_per_day: Average messages per day
        avg_message_length: Average tokens per message
        personas: Number of personas
        model: Model name
    """
    # Pricing per 1M tokens (input/output)
    pricing = {
        "gpt-4-turbo": (10, 30),
        "gpt-3.5-turbo": (0.5, 1.5),
        "claude-3-5-sonnet": (3, 15),
        "claude-3-haiku": (0.25, 1.25),
        "gemini-1.5-flash": (0.075, 0.3),
    }

    if model not in pricing:
        return "Unknown model"

    input_price, output_price = pricing[model]

    # Calculate tokens
    daily_messages = messages_per_day * personas
    monthly_messages = daily_messages * 30

    input_tokens = monthly_messages * avg_message_length
    output_tokens = monthly_messages * avg_message_length * 1.5  # Assume 1.5x output

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost

    return {
        "monthly_messages": monthly_messages,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

# Example
costs = estimate_monthly_cost(
    messages_per_day=100,
    avg_message_length=200,
    personas=3,
    model="gpt-3.5-turbo"
)
print(f"Estimated monthly cost: ${costs['total_cost']:.2f}")
```

### Cost Comparison

| Scenario | GPT-4 | GPT-3.5 | Claude 3.5 | Gemini Flash | Ollama (Local) |
|----------|-------|---------|------------|--------------|----------------|
| Light (10 msg/day) | $12 | $0.50 | $5 | $0.15 | $0 |
| Medium (50 msg/day) | $60 | $2.50 | $25 | $0.75 | $0 |
| Heavy (200 msg/day) | $240 | $10 | $100 | $3 | $0 |

Based on 3 personas, 200 tokens/message average.

---

## Performance Comparison

### Latency Comparison

| Provider | First Token | Full Response | Streaming |
|----------|-------------|---------------|-----------|
| Ollama (Local, GPU) | 50-200ms | 2-10s | ✅ Yes |
| OpenAI GPT-3.5 | 200-500ms | 3-8s | ✅ Yes |
| OpenAI GPT-4 | 500-1000ms | 10-30s | ✅ Yes |
| Claude 3.5 Sonnet | 300-700ms | 5-15s | ✅ Yes |
| Gemini Flash | 100-300ms | 2-5s | ✅ Yes |

### Throughput Comparison

| Provider | Concurrent Requests | Rate Limits |
|----------|-------------------|-------------|
| Ollama (Local) | Limited by GPU | No limits |
| OpenAI | High | 3,500 RPM (tier 1) |
| Anthropic | Medium | 50 RPM (free tier) |
| Google | High | 60 RPM (free tier) |

---

## Migration Guide

### From Ollama to OpenAI

1. Install OpenAI SDK:
   ```bash
   uv pip install openai>=1.0.0
   ```

2. Set environment variables:
   ```env
   LLM_BACKEND=openai
   OPENAI_API_KEY=sk-your-key
   ```

3. Update model names in personas:
   - `llama2:7b` → `gpt-3.5-turbo`
   - `llama2:13b` → `gpt-4-turbo-preview`

4. Test connection in UI

5. Monitor costs in OpenAI dashboard

### From OpenAI to Ollama

1. Install Ollama:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. Pull models:
   ```bash
   ollama pull llama2:7b
   ```

3. Update environment:
   ```env
   LLM_BACKEND=ollama
   OLLAMA_URL=http://localhost:11434
   ```

4. Update model names in personas

### Hybrid Deployment

Use different backends for different personas:

```python
# Per-persona backend selection
class Persona:
    def __init__(self, name, backend="ollama", model="llama2:7b"):
        self.name = name
        self.backend = backend
        self.model = model

# Example: Fast responses with Ollama, quality with Claude
personas = [
    Persona("FastBot", backend="ollama", model="llama2:7b"),
    Persona("QualityBot", backend="anthropic", model="claude-3-5-sonnet"),
    Persona("CheapBot", backend="gemini", model="gemini-1.5-flash")
]
```

---

## Additional Resources

- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Documentation](https://docs.anthropic.com/)
- [Google AI Documentation](https://ai.google.dev/)
- [Deployment Guide](DEPLOYMENT.md)
- [Production Setup](PRODUCTION_SETUP.md)

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
