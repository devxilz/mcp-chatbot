# app/services/llm_service.py
import requests

class LLMService:
    def __init__(self, model_name="llama3.2:3b"):
        # Local Ollama generate API endpoint
        self.url = "http://localhost:11434/api/generate"
        self.model_name = model_name

    def generate_reply(self, context_items, query):
        # Build final prompt
        prompt = self._build_prompt(context_items, query)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        # Send request to local Ollama server
        response = requests.post(self.url, json=payload)
        data = response.json()

        # `response` field contains model output
        return data.get("response", "").strip()

    def _build_prompt(self, context_items, query):
        """
        Creates a combined prompt of:
        - user profile
        - long-term memories
        - recent chat messages
        - user question
        """
        final_context = ""

        # Add all context items
        for item in context_items:
            final_context += f"{item['text']}\n"

        # Add the current question
        final_context += f"\nUser question: {query}\n"

        return final_context
