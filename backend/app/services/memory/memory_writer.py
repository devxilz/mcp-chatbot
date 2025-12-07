import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

class MemoryWriteDecision:
    def __init__(self, action: str, reason: str, memory_type=None, importance=None, summary=None):
        self.action = action
        self.reason = reason
        self.memory_type = memory_type
        self.importance = importance
        self.summary = summary


class MemoryWriter:
    """
    Intelligent AI-powered Memory Writer.
    Decides:
    - Should a message be stored?
    - Should it be summarized first?
    - What type of memory is it? (personal info, preference, goal, fact, task, etc.)
    - How important is the message? (0–1)
    """

    def __init__(self, memory_engine, llm_service):
        self.memory_engine = memory_engine
        self.llm = llm_service

        # Hard filters
        self.noise_words = {
            "ok", "k", "kk", "lol", "yes", "no", "hmm", "thanks",
            "thank you", "hi", "hello", "hey", "yo"
        }

    # -------------------------------------------------------------
    # Detect trivial messages we should NEVER save
    # -------------------------------------------------------------
    def is_noise(self, text: str) -> bool:
        clean = text.lower().strip()
        if clean in self.noise_words:
            return True
        if len(clean.split()) < 3:
            return True
        return False

    # -------------------------------------------------------------
    # LLM classification: memory_type + importance score
    # -------------------------------------------------------------
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

Return ONLY JSON like:
{{
  "type": "...",
  "importance": 0.0
}}

Message:
\"\"\"{text}\"\"\"        
"""

        response = self.llm.generate_reply([], prompt)

        try:
            data = json.loads(response)
            mtype = data.get("type", "fact")
            importance = float(data.get("importance", 0.4))
        except:
            mtype = "fact"
            importance = 0.4

        return {"type": mtype, "importance": importance}

    # -------------------------------------------------------------
    # Summarize long messages
    # -------------------------------------------------------------
    def summarize(self, text: str) -> str:
        return self.llm.summarize(text, max_tokens=40)

    # -------------------------------------------------------------
    # Main decision system
    # -------------------------------------------------------------
    def decide(self, user_id: str, session_id: str, role: str, text: str):
        # Only store user messages
        if role != "user":
            return MemoryWriteDecision("ignore", "assistant/system messages ignored")

        # Filter noise
        if self.is_noise(text):
            return MemoryWriteDecision("ignore", "noise/too short")

        # Classify memory
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

        # Default store
        return MemoryWriteDecision(
            action="store",
            reason="informative message",
            memory_type=mem_type,
            importance=importance
        )

    # -------------------------------------------------------------
    # Execute the decision via MemoryEngine
    # -------------------------------------------------------------
    def execute(self, decision: MemoryWriteDecision, user_id, session_id, text):
        if decision.action == "ignore":
            return None

        if decision.action == "compress_store":
            content = decision.summary
        else:
            content = text

        return self.memory_engine.add_memory(
            user_id=user_id,
            session_id=session_id,
            text=content,
            memory_type=decision.memory_type,
            metadata={"importance": decision.importance}
        )
