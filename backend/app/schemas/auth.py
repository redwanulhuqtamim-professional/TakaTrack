from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def verify_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if not any(c.isdigit() for c in self.password) or not any(c.isalpha() for c in self.password):
            raise ValueError("Password must contain at least one letter and one number.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def verify_new_passwords(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        return self


class OnboardingRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    initial_monthly_budget: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    opening_cash: Optional[Decimal] = Field(Decimal("0.00"), ge=Decimal("0.00"))


class UserSettingsResponse(BaseModel):
    currency: str
    timezone: str
    preferred_dashboard_month: Optional[str] = None
    daily_spending_target: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_onboarded: bool
    created_at: datetime
    settings: Optional[UserSettingsResponse] = None

    model_config = {"from_attributes": True}
