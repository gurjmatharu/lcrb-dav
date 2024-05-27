from datetime import datetime
from typing import TypedDict

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class HealthCheck(BaseModel):
    name: str
    version: str
    description: str


class StatusMessage(BaseModel):
    status: bool
    message: str


class UUIDModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}


class TimestampModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GenericErrorMessage(BaseModel):
    detail: str


# Currently used as a TypedDict since it can be used as a part of a
# Pydantic class but a Pydantic class can not inherit from TypedDict
# and and BaseModel
class RevealedAttribute(TypedDict, total=False):
    sub_proof_index: int
    values: dict


class AgeVerificationModelCreate(BaseModel):
    notify_endpoint: str | None
    metadata: dict | None

    class Config:
        schema_extra = {
            "example": {
                "notify_endpoint": "https://my-url/webhook#api-key",
                "metadata": {"other_system_id": 123},
            }
        }


class AgeVerificationModelRead(AgeVerificationModelCreate):
    status: str
    id: str


class AgeVerificationModelCreateRead(AgeVerificationModelRead):
    url: str
