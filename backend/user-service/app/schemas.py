
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime


class FamilyCreate(BaseModel):
    name: str


class FamilyResponse(BaseModel):
    id: int
    name: str
    invite_code: str

    model_config = ConfigDict(from_attributes=True)


class FamilyAdminResponse(BaseModel):
    id: int
    name: str
    members_count: int
    head_email: Optional[str] = "Немає голови родини"
    head_emails: Optional[list[str]] = None
    last_activity_at: datetime
    is_inactive: bool
    can_be_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    invite_code: str | None = None
    family_name: str | None = None
    create_family: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    family_id: Optional[int] = None
    family_invite_code: Optional[str] = None
    access_token: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    has_password: bool = True

class GoogleRegistrationComplete(BaseModel):
    registration_token: str
    password: str = Field(min_length=6)
    username: Optional[str] = None

    create_family: bool = False
    family_name: Optional[str] = None
    invite_code: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: Optional[str] = None
    new_password: str = Field(min_length=6)