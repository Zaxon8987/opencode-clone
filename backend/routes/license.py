from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from license import validate_license, get_features_for_tier

router = APIRouter(prefix="/license", tags=["license"])


class ValidateRequest(BaseModel):
    key: str
    tool: str | None = None


@router.post("/validate")
async def validate(data: ValidateRequest):
    lic = validate_license(data.key)
    if not lic:
        raise HTTPException(403, "Invalid or expired license key")
    tier = lic["tier"]
    features = get_features_for_tier(tier)
    if data.tool and data.tool not in features:
        raise HTTPException(403, f"Feature '{data.tool}' not available on {tier} tier")
    return {
        "valid": True,
        "tier": tier,
        "user": {"email": lic["email"], "name": lic["name"]},
        "features": features,
    }


@router.get("/features/{tier}")
async def features(tier: str):
    features = get_features_for_tier(tier)
    return {"tier": tier, "features": features}
