import json
import logging
from typing import List, Optional

from pydantic import BaseModel, ValidationError, Field

from app.services.llm.llm_service import LLMService
from app.core.user_profile_store import UserProfileStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Pydantic schema (stable structure + validation)
# ---------------------------------------------------
class ExtractedProfile(BaseModel):
    name: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)

    # NEW: properly used personal_info
    personal_info: List[str] = Field(default_factory=list)


    class Config:
        extra = "ignore"


class ProfileExtractor:
    """
    Final, improved version of the profile extraction subsystem.
    """

    MAX_PREFERENCES = 200
    MAX_GOALS = 200
    MAX_FACTS = 500
    MAX_PERSONAL_INFO = 500

    def __init__(self):
        self.llm = LLMService()
        self.store = UserProfileStore()

    # ============================================================
    # Main API
    # ============================================================
    def extract_and_update(self, user_id: str, message: str):
        """
        Main entrypoint for profile extraction.
        """

        system_prompt = (
            "You are an information extraction model. "
            "You MUST return only valid JSON. No explanations, no text outside JSON. "
            "Follow the schema exactly."
        )

        user_prompt = self._build_prompt(message)

        raw_response = self.llm.generate_reply(
            [{"role": "system", "content": system_prompt}],
            user_prompt
        )

        # Parse JSON robustly
        data = self._parse_llm_json(raw_response)
        if data is None:
            logger.warning("ProfileExtractor: Invalid JSON returned for user %s", user_id)
            return None

        # Schema validation
        try:
            extracted = ExtractedProfile(**data)
        except ValidationError as e:
            logger.warning("ProfileExtractor: Schema validation error: %s", e)
            return None

        # If the extractor returned nothing useful, skip update
        if not (
            extracted.name or
            extracted.preferences or
            extracted.goals or
            extracted.facts or
            extracted.personal_info
        ):
            return None



        # Load profile
        profile = self.store.load_profile(user_id) or {}

        # Apply updates
        self._update_name(profile, extracted)
        self._merge_list(profile, "preferences", extracted.preferences, normalize=True, lower=True)
        self._merge_list(profile, "goals", extracted.goals)
        self._merge_list(profile, "facts", extracted.facts)
        self._merge_list(profile, "personal_info", extracted.personal_info)

        # Enforce caps
        self._enforce_limits(profile)

        # Save
        self.store.save_profile(user_id, profile)

        logger.info("ProfileExtractor: Updated profile for user %s", user_id)
        return profile

    # ============================================================
    # Prompt Builder
    # ============================================================
    def _build_prompt(self, message: str) -> str:
        """
        Improved extraction instructions.
        """

        return f"""
Extract personal information about the USER from the message.

STRICT RULES:
1. Do NOT infer or invent anything. Only extract what the user explicitly says.
2. Extract a name ONLY if the user says:
   - "I am <name>"
   - "I'm <name>"
   - "My name is <name>"
   - "Call me <name>"
3. Extract USER preferences:
   - "I like football" → ["football"]
   - "I enjoy coding" → ["coding"]
   Do NOT extract preferences of OTHER people.
4. Extract USER goals:
   - "I want to learn AI"
   - "My goal is to get a job"
5. Extract USER facts:
   - "I have a sister named Jiya"
   - "I study in class 12"
6. Extract USER personal_info:
   Personal biographical details:
   - family relationships (e.g., "My father is Raj")
   - location (ONLY if explicitly stated)
   - age (ONLY if explicitly stated)
   - background, lifestyle details
   - anything that describes who the user IS, not what they like.
7. Use update_profile = true if ANY of the above exist.

RETURN STRICT JSON with EXACT keys:
{{
  "name": null or string,
  "preferences": list of strings,
  "goals": list of strings,
  "facts": list of strings,
  "personal_info": list of strings,
  "update_profile": true or false
}}

NO explanations. NO extra text. ONLY JSON.

User message:
\"\"\"{message}\"\"\"
""".strip()

    # ============================================================
    # JSON Extraction
    # ============================================================
    def _parse_llm_json(self, raw: str) -> Optional[dict]:
        if not raw:
            return None
        raw = raw.strip()

        # Try direct JSON
        try:
            return json.loads(raw)
        except:
            pass

        # Extract JSON from code blocks anywhere
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{") and part.endswith("}"):
                    try:
                        return json.loads(part)
                    except:
                        pass

        # Extract first {...} block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            subset = raw[start:end + 1]
            try:
                return json.loads(subset)
            except:
                return None

        return None

    # ============================================================
    # Helpers
    # ============================================================
    def _update_name(self, profile: dict, extracted: ExtractedProfile):
        if extracted.name:
            cleaned = extracted.name.strip()
            if cleaned:
                profile["name"] = cleaned

    def _merge_list(self, profile: dict, key: str, new_values: List[str], normalize=False, lower=False):
        if not new_values:
            return

        current = profile.get(key, [])
        if not isinstance(current, list):
            current = []

        def norm(s: str):
            s = s.strip()
            if lower:
                s = s.lower()
            return s

        if normalize:
            combined = {norm(x) for x in current if isinstance(x, str)}
            combined |= {norm(x) for x in new_values if isinstance(x, str)}
            profile[key] = list(combined)
        else:
            # simpler merge
            for x in new_values:
                if isinstance(x, str) and x not in current:
                    current.append(x)
            profile[key] = current

    def _enforce_limits(self, profile: dict):
        def cap(field: str, limit: int):
            lst = profile.get(field)
            if isinstance(lst, list) and len(lst) > limit:
                profile[field] = lst[-limit:]

        cap("preferences", self.MAX_PREFERENCES)
        cap("goals", self.MAX_GOALS)
        cap("facts", self.MAX_FACTS)
        cap("personal_info", self.MAX_PERSONAL_INFO)
