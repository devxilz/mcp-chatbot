import json
import logging
import re
from typing import Dict, Any, Optional


class MemoryWriteDecision:
    def __init__(self, action: str, reason: str, memory_type=None, importance=None, summary=None):
        self.action = action
        self.reason = reason
        self.memory_type = memory_type
        self.importance = importance
        self.summary = summary


class MemoryWriter:
    """
    Production-grade Memory Writer with:
    - Noise filtering
    - Robust JSON-safe classification
    - Memory type validation
    - Importance clamping
    - Automatic retry for bad LLM output
    - Clean fallback logic
    """

    ALLOWED_TYPES = {
        "personal_info",
        "preference",
        "goal",
        "task",
        "fact",
        "irrelevant"
    }

    def __init__(self, memory_engine, llm_service):
        self.memory_engine = memory_engine
        self.llm = llm_service

        self.noise_words = {
            "ok", "k", "kk", "lol", "yes", "no", "hmm", "thanks",
            "thank you", "hi", "hello", "hey", "yo"
        }

    # ===============================================================
    # Noise Filter — improved (less destructive)
    # ===============================================================
    def is_noise(self, text: str) -> bool:
        clean = text.lower().strip()

        # 1. Hard noise words
        if clean in self.noise_words:
            return True

        # 2. Allow short but meaningful messages such as:
        # "I'm vegan", "I'm 20", "Love coffee", "From India"
        # So we only reject single-word non-info messages
        if len(clean.split()) == 1:
            return True

        return False

    # ===============================================================
    # Robust JSON parsing with extraction + retry + fallback
    # ===============================================================
    def _safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None

        text = text.strip()

        # Try direct JSON
        try:
            return json.loads(text)
        except:
            pass

        # Try extracting JSON object from text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except:
                return None

        return None

    # ===============================================================
    # LLM Classification — JSON robust version
    # ===============================================================
    def classify_and_score(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Classify the user's message into one of these types:
- personal_info
- preference
- goal
- task
- fact
- irrelevant

Also assign an importance score between 0.0 and 1.0.

Return ONLY valid JSON:
{{
  "type": "...",
  "importance": 0.0
}}

Message:
\"\"\"{text}\"\"\"
"""

        # Try first attempt
        response = self.llm.generate_reply([], prompt)
        data = self._safe_parse_json(response)

        # Retry with stronger prompt if bad JSON
        if data is None:
            retry_prompt = f"""
Return ONLY this JSON structure with no extra text:
{{"type": "", "importance": 0.0}}

Message: \"{text}\"
"""
            retry_response = self.llm.generate_reply([], retry_prompt)
            data = self._safe_parse_json(retry_response)

        # Final fallback
        if data is None:
            logging.warning("MemoryWriter: Failed LLM classification → fallback defaults.")
            return {"type": "fact", "importance": 0.4}

        # Validate type
        mtype = data.get("type", "fact")
        if mtype not in self.ALLOWED_TYPES:
            logging.warning(f"Invalid memory type from LLM: {mtype} → replacing with 'fact'")
            mtype = "fact"

        # Validate importance
        importance = data.get("importance", 0.4)
        try:
            importance = float(importance)
        except:
            importance = 0.4

        # Clamp importance
        importance = max(0.0, min(importance, 1.0))

        return {"type": mtype, "importance": importance}

    # ===============================================================
    # Summarization
    # ===============================================================
    def summarize(self, text: str) -> str:
        # Protect against LLM returning empty or None
        try:
            summary = self.llm.summarize(text, max_tokens=40)
            return summary.strip() if summary else text[:200]
        except Exception:
            logging.warning("MemoryWriter: summarization failed → fallback to truncated text")
            return text[:200]

    # ===============================================================
    # Main Decision Logic
    # ===============================================================
    def decide(self, user_id: str, session_id: str, role: str, text: str):
        if role != "user":
            return MemoryWriteDecision("ignore", "assistant/system messages ignored")

        if self.is_noise(text):
            return MemoryWriteDecision("ignore", "noise/too uninformative")

        # Classification (type + importance)
        result = self.classify_and_score(text)
        mem_type = result["type"]
        importance = result["importance"]

        if mem_type == "irrelevant":
            return MemoryWriteDecision("ignore", "classified irrelevant")

        # Summarize long messages
        if len(text.split()) > 30:
            summary = self.summarize(text)
            return MemoryWriteDecision(
                action="compress_store",
                reason="long message summarized",
                memory_type=mem_type,
                importance=importance,
                summary=summary
            )

        # Normal informative store
        return MemoryWriteDecision(
            action="store",
            reason="informative message",
            memory_type=mem_type,
            importance=importance
        )

    # ===============================================================
    # Execute Write
    # ===============================================================
    def execute(self, decision: MemoryWriteDecision, user_id, session_id, text):
        if decision.action == "ignore":
            return None

        content = decision.summary if decision.action == "compress_store" else text

        try:
            return self.memory_engine.add_memory(
                user_id=user_id,
                session_id=session_id,
                text=content,
                memory_type=decision.memory_type,
                metadata={"importance": decision.importance}
            )
        except Exception as e:
            logging.error(f"MemoryWriter: Failed to write memory → {e}")
            return None
