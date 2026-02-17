"""
Consent Models for DPDP Act Compliance
Digital Personal Data Protection Act 2023 compliance models.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class ConsentPurpose(str):
    """Valid consent purposes as per DPDP Act."""
    TRAVEL_PLANNING = "travel_planning"
    PERSONALIZATION = "personalization"
    MARKETING = "marketing"
    ANALYTICS = "analytics"


class ConsentRecord(BaseModel):
    """
    Consent record stored in MongoDB.
    Tracks user consent for specific data processing purposes.
    """
    user_id: str
    purpose: Literal["travel_planning", "personalization", "marketing", "analytics"]
    purpose_version: str = "1.0"  # Version of T&C/privacy policy
    consented: bool
    consent_timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    withdrawal_timestamp: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "purpose": "travel_planning",
                "purpose_version": "1.0",
                "consented": True,
                "consent_timestamp": "2026-02-07T11:30:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0..."
            }
        }


class ConsentRequest(BaseModel):
    """Request body for recording consent."""
    purposes: list[str] = Field(..., description="List of purposes to consent to")
    agreed: bool = Field(..., description="Whether user agreed to all purposes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "purposes": ["travel_planning", "personalization"],
                "agreed": True
            }
        }


class ConsentWithdrawalRequest(BaseModel):
    """Request body for withdrawing consent."""
    purpose: str = Field(..., description="Purpose to withdraw consent from")
    
    class Config:
        json_schema_extra = {
            "example": {
                "purpose": "marketing"
            }
        }


class ConsentResponse(BaseModel):
    """Response after recording consent."""
    status: str
    timestamp: datetime
    purposes_recorded: list[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "recorded",
                "timestamp": "2026-02-07T11:30:00Z",
                "purposes_recorded": ["travel_planning", "personalization"]
            }
        }


class UserConsents(BaseModel):
    """
    User's current consent status for all purposes.
    Used in API responses to show user their consent state.
    """
    user_id: str
    consents: dict[str, bool]  # purpose -> is_active
    last_updated: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "consents": {
                    "travel_planning": True,
                    "personalization": True,
                    "marketing": False
                },
                "last_updated": "2026-02-07T11:30:00Z"
            }
        }
