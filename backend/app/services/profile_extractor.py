import json
from app.services.llm.llm_service import LLMService
from app.core.user_profile_store import UserProfileStore


class ProfileExtractor:
    """
    Extracts personal information from user messages using the LLM.
    Automatically updates the user's profile.
    """

    def __init__(self):
        self.llm = LLMService()
        self.store = UserProfileStore()

    # ---------------------------------------------------------
    # Extract profile info and update DB
    # ---------------------------------------------------------
    def extract_and_update(self, user_id: str, message: str):
        """
        Ask LLM to extract personal attributes:
        - name
        - preferences
        - goals
        - facts
        """

        prompt = f"""
Extract ONLY personal information from the following message.
Do NOT infer or invent anything.

Return JSON with EXACT keys:
{{
  "name": null or string,
  "preferences": list of strings,
  "goals": list of strings,
  "facts": list of strings,
  "update_profile": true or false
}}

If no personal information is present, return:
{{"update_profile": false}}

User message:
\"\"\"{message}\"\"\"        
"""

        # Step 1: get LLM response
        response = self.llm.generate_reply([], prompt)

        # Step 2: try reading JSON
        try:
            data = json.loads(response)
        except:
            return None  # fail silently

        if not data.get("update_profile"):
            return None

        # Step 3: load existing profile
        profile = self.store.load_profile(user_id) or {}

        # Step 4: update fields safely
        if data.get("name"):
            profile["name"] = data["name"]

        if data.get("preferences"):
            old = set(profile.get("preferences", []))
            profile["preferences"] = list(old.union(set(data["preferences"])))

        if data.get("goals"):
            old = set(profile.get("goals", []))
            profile["goals"] = list(old.union(set(data["goals"])))

        if data.get("facts"):
            old = set(profile.get("facts", []))
            profile["facts"] = list(old.union(set(data["facts"])))

        # Step 5: save back to DB
        self.store.save_profile(user_id, profile)

        return profile
