from fastapi import APIRouter, HTTPException
from app.core.user_profile_store import UserProfileStore

router = APIRouter(tags=["User Profile"])

profile_store = UserProfileStore()


@router.get("/profile/{user_id}")
def get_profile(user_id: str):
    profile = profile_store.load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"user_id": user_id, "profile": profile}


@router.post("/profile/{user_id}")
def create_or_replace_profile(user_id: str, profile: dict):
    profile_store.save_profile(user_id, profile)
    return {"status": "success", "message": "Profile saved", "profile": profile}


@router.patch("/profile/{user_id}")
def update_profile_field(user_id: str, updates: dict):
    profile = profile_store.load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in updates.items():
        profile_store.update_field(user_id, field, value)

    updated = profile_store.load_profile(user_id)
    return {"status": "success", "updated_profile": updated}


@router.delete("/profile/{user_id}")
def delete_profile(user_id: str):
    # We simply overwrite with empty JSON
    profile_store.save_profile(user_id, {})
    return {"status": "success", "message": "Profile cleared"}
