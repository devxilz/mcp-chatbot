# app/services/llm/llm_service.py

import json
import httpx


class LLMService:
    def __init__(self, model_name="llama3.2:3b"):
        self.base_url = "http://localhost:11434"
        self.model_name = model_name

    # ---------------------------------------------------------
    # SYNC Reply (non-streaming, used for normal chat)
    # ---------------------------------------------------------
    def generate_reply(self, context_items, query: str) -> str:

        prompt = self.build_prompt(context_items, query)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        response = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=None)
        data = response.json()

        return data.get("response", "").strip()

    # ---------------------------------------------------------
    # ASYNC STREAMING REPLY (token-by-token streaming)
    # ---------------------------------------------------------
    async def stream_reply(self, context_items, query):
        prompt = self.build_prompt(context_items, query)
        url = "http://localhost:11434/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    
                    # Skip empty lines
                    if not line or not line.strip():
                        continue

                    # Attempt JSON parse safely
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Handle errors from Ollama
                    if "error" in data:
                        yield f"[LLM ERROR] {data['error']}"
                        continue

                    # Stop when done
                    if data.get("done"):
                        break

                    # Get streamed text safely
                    chunk = data.get("response")
                    if chunk:
                        yield chunk
    # ---------------------------------------------------------
    # Summarization API (used by MemoryWriter)
    # ---------------------------------------------------------
    def summarize(self, text: str, max_tokens=60) -> str:

        prompt = (
            "Summarize the following text in a short, clear way.\n"
            f"Text: {text}\nSummary:"
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        response = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=None)
        data = response.json()

        return data.get("response", "").strip()

    # ---------------------------------------------------------
    # Prompt Builder
    # ---------------------------------------------------------
    def build_prompt(self, context_items, query: str) -> str:
        """
        Context items are strings (NOT dicts).
        """
        final_context = ""

        for item in context_items:
            final_context += f"{item}\n"

        final_context += f"\nUser question: {query}\n"

        return final_context
