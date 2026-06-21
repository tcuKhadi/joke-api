"""Local GGUF model inference via llama-cpp-python."""

import time

from llama_cpp import Llama

from app.core.config import settings


class LLMService:
    """Wraps a locally loaded GGUF model for text generation."""

    def __init__(self) -> None:
        self._llm = Llama(
            model_path=settings.llm_model_path,
            n_ctx=settings.llm_n_ctx,
            n_threads=settings.llm_n_threads,
            n_gpu_layers=settings.llm_n_gpu_layers,
            verbose=False,
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.9,
        top_p: float = 0.95,
        max_tokens: int = 200,
    ) -> dict:
        """Run inference and return output with timing/token metadata."""
        start = time.monotonic()

        result = self._llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

        latency_ms = int((time.monotonic() - start) * 1000)

        return {
            "text": result["choices"][0]["message"]["content"],
            "latency_ms": latency_ms,
            "prompt_tokens": result["usage"]["prompt_tokens"],
            "completion_tokens": result["usage"]["completion_tokens"],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }


llm_service = LLMService()